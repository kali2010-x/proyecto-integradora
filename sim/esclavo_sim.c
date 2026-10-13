/* esclavo_sim.c - Simula el ESP32 en el PC o en la propia Raspberry (sin hardware).
 * Emula el bus I2C por TCP: 'W'+trama = escritura del maestro, 'R' = lectura.
 * Usa EXACTAMENTE el mismo enlace.c y cliente_tls.c que el firmware del ESP32.
 * Uso: ./esclavo_sim certs/servidor.pem [puerto] [eco]
 *   'eco' = modo prueba de eco (devuelve cada trama tal cual, como MODO_ECO del ESP32) */
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <unistd.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <sys/socket.h>
#include "enlace.h"
#include "plataforma.h"
#include "cliente_tls.h"

static pthread_mutex_t mtx = PTHREAD_MUTEX_INITIALIZER, mcv = PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t cv = PTHREAD_COND_INITIALIZER;
static void lk(void) { pthread_mutex_lock(&mtx); }
static void ulk(void) { pthread_mutex_unlock(&mtx); }
static void avisar(void) { pthread_mutex_lock(&mcv); pthread_cond_broadcast(&cv); pthread_mutex_unlock(&mcv); }
static void esperar(int ms) {
    struct timespec ts; clock_gettime(CLOCK_REALTIME, &ts);
    ts.tv_nsec += (long)ms * 1000000L; ts.tv_sec += ts.tv_nsec / 1000000000L; ts.tv_nsec %= 1000000000L;
    pthread_mutex_lock(&mcv); pthread_cond_timedwait(&cv, &mcv, &ts); pthread_mutex_unlock(&mcv);
}
uint64_t plat_us(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return (uint64_t)t.tv_sec * 1000000ULL + t.tv_nsec / 1000; }
void plat_esperar_rx(int ms) { esperar(ms); }
void plat_esperar_tx(int ms) { esperar(ms); }
uint32_t plat_heap_libre(void) { return 0; }
uint32_t plat_stack_libre(void) { return 0; }
void plat_log(const char *fmt, ...) { va_list a; va_start(a, fmt); vprintf(fmt, a); va_end(a); fflush(stdout); }

static void *hilo_app(void *arg) { (void)arg; cliente_tls_bucle(); return NULL; }

static int leer_n(int fd, uint8_t *b, int n) {
    int r = 0; while (r < n) { int k = (int)recv(fd, b + r, n - r, 0); if (k <= 0) return -1; r += k; } return r;
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "uso: %s cert_servidor.pem [puerto]\n", argv[0]); return 1; }
    FILE *f = fopen(argv[1], "rb"); if (!f) { perror("cert"); return 1; }
    static char ca[8192]; int ca_len = (int)fread(ca, 1, sizeof ca, f); fclose(f);
    int puerto = argc > 2 ? atoi(argv[2]) : 5555;
    int modo_eco = argc > 3 && strcmp(argv[3], "eco") == 0;

    enlace_plataforma_t p = { lk, ulk, avisar, avisar, avisar };
    enlace_init(&p);
    cliente_tls_init(ca, ca_len);
    pthread_t th; pthread_create(&th, NULL, hilo_app, NULL);

    int s = socket(AF_INET, SOCK_STREAM, 0), uno = 1;
    setsockopt(s, SOL_SOCKET, SO_REUSEADDR, &uno, sizeof uno);
    struct sockaddr_in a = {0}; a.sin_family = AF_INET; a.sin_port = htons(puerto); a.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    if (bind(s, (struct sockaddr *)&a, sizeof a) || listen(s, 1)) { perror("bind"); return 1; }
    printf("esclavo simulado escuchando en 127.0.0.1:%d (FRAME_SIZE=%d)%s\n", puerto, FRAME_SIZE, modo_eco ? " MODO ECO" : ""); fflush(stdout);
    for (;;) {
        int c = accept(s, NULL, NULL); if (c < 0) continue;
        setsockopt(c, IPPROTO_TCP, TCP_NODELAY, &uno, sizeof uno);
        uint8_t cmd, trama[FRAME_SIZE], resp[FRAME_SIZE]; memset(resp, 0, sizeof resp);
        while (leer_n(c, &cmd, 1) == 1) {
            if (cmd == 'W') {                           /* equivale a on_receive + tarea de enlace */
                if (leer_n(c, trama, FRAME_SIZE) < 0) break;
                if (modo_eco) memcpy(resp, trama, FRAME_SIZE);
                else { enlace_procesar_trama_maestro(trama, FRAME_SIZE); enlace_construir_respuesta(resp); }
            } else if (cmd == 'R') {                    /* el maestro lee la respuesta preparada */
                if (send(c, resp, FRAME_SIZE, 0) != FRAME_SIZE) break;
            }
        }
        close(c);
    }
}
