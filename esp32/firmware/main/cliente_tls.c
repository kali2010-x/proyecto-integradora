/* cliente_tls.c - Cliente TLS 1.3 (wolfSSL, interfaz compatible con OpenSSL) sobre el enlace I2C.
 * Código portable: se usa igual en el ESP32 y en el simulador del PC. */
#ifdef WOLFSSL_USER_SETTINGS
#include <wolfssl/wolfcrypt/settings.h>
#else
#include <wolfssl/options.h>
#endif
#include <wolfssl/ssl.h>
#include <wolfssl/openssl/ssl.h>
#include <stdio.h>
#include <string.h>
#include "enlace.h"
#include "plataforma.h"
#include "cliente_tls.h"

/* Códigos IANA de los grupos TLS (iguales en wolfSSL y OpenSSL). wolfSSL 5.8 llama al híbrido
 * WOLFSSL_X25519_ML_KEM_768 y 5.9 WOLFSSL_X25519MLKEM768; el número es el mismo. */
#define GRUPO_TLS_X25519MLKEM768 4588   /* 0x11EC */
#define GRUPO_TLS_X25519           29   /* 0x001D */

#define TIMEOUT_IO_MS 15000
static const char *g_ca; static int g_ca_len;

/* ---------- E/S de wolfSSL sobre el enlace (bloqueante con timeout) ---------- */
static int io_recv(WOLFSSL *ssl, char *buf, int sz, void *ctx) {
    (void)ssl; (void)ctx;
    uint64_t fin = plat_us() + (uint64_t)TIMEOUT_IO_MS * 1000;
    for (;;) {
        int n = enlace_rx_leer((uint8_t *)buf, sz);
        if (n > 0) return n;
        if (plat_us() > fin) return WOLFSSL_CBIO_ERR_TIMEOUT;
        plat_esperar_rx(5);
    }
}
static int io_send(WOLFSSL *ssl, char *buf, int sz, void *ctx) {
    (void)ssl; (void)ctx;
    int env = 0; uint64_t fin = plat_us() + (uint64_t)TIMEOUT_IO_MS * 1000;
    while (env < sz) {
        int n = enlace_tx_escribir((const uint8_t *)buf + env, sz - env);
        env += n;
        if (env < sz) { if (plat_us() > fin) return WOLFSSL_CBIO_ERR_TIMEOUT; plat_esperar_tx(5); }
    }
    return sz;
}
/* Para el modo sin TLS (control): mismas funciones sin wolfSSL */
static int raw_write(const uint8_t *p, int n) { return io_send(NULL, (char *)p, n, NULL); }
static int raw_read_exacto(uint8_t *p, int n) {
    int r = 0; while (r < n) { int k = io_recv(NULL, (char *)p + r, n - r, NULL); if (k < 0) return k; r += k; }
    return r;
}
/* Código de error negativo para el reporte (los códigos internos de wolfSSL ya son negativos) */
static int cod_error(WOLFSSL *ssl, int ret) {
    int e = wolfSSL_get_error(ssl, ret);
    return e < 0 ? e : -1000 - e;
}
static int tls_read_exacto(WOLFSSL *ssl, uint8_t *p, int n) {
    int r = 0;
    while (r < n) {
        int k = SSL_read(ssl, p + r, n - r);
        if (k <= 0) return cod_error(ssl, k);
        r += k;
    }
    return r;
}

/* ---------- Mensajes de control ---------- */
typedef struct { uint8_t grupo; uint16_t msg, n_msgs, run_id; uint32_t bulk; } orden_t;
typedef struct { int16_t estado; uint32_t t_hs, rtt_media, rtt_max, bulk_us, heap_usado, stack_libre, heap_libre; } reporte_t;

static int leer_orden(orden_t *o) {
    uint8_t m[MAX_PAYLOAD]; int n = enlace_ctrl_pop(m, sizeof m);
    if (n < 12 || m[0] != 'S') return 0;
    o->grupo = m[1]; o->msg = (m[2] << 8) | m[3]; o->n_msgs = (m[4] << 8) | m[5];
    o->bulk = ((uint32_t)m[6] << 24) | ((uint32_t)m[7] << 16) | (m[8] << 8) | m[9];
    o->run_id = (m[10] << 8) | m[11];
    return 1;
}
static void put16(uint8_t *p, uint32_t v) { p[0] = v >> 8; p[1] = v; }
static void put32(uint8_t *p, uint32_t v) { p[0] = v >> 24; p[1] = v >> 16; p[2] = v >> 8; p[3] = v; }
static void enviar_reporte(uint16_t run, const reporte_t *r) {
    uint8_t a[17], b[19];               /* dos mensajes: caben en tramas de 32 bytes */
    a[0] = 'R'; put16(a + 1, (uint16_t)r->estado); put16(a + 3, run);
    put32(a + 5, r->t_hs); put32(a + 9, r->rtt_media); put32(a + 13, r->rtt_max);
    b[0] = 'Q'; put16(b + 1, run); put32(b + 3, r->bulk_us); put32(b + 7, r->heap_usado);
    put32(b + 11, r->stack_libre); put32(b + 15, r->heap_libre);
    for (int i = 0; i < 50 && !enlace_tx_vacio(); i++) plat_esperar_tx(20);
    while (!enlace_tx_ctrl(a, sizeof a)) plat_esperar_tx(5);
    while (!enlace_tx_ctrl(b, sizeof b)) plat_esperar_tx(5);
}

static void armar_mensaje(uint8_t *m, int n, uint16_t run, int i) {
    memset(m, 'x', n);
    char cab[40]; int k = snprintf(cab, sizeof cab, "TELEMETRIA|run=%u|i=%d|", run, i);
    memcpy(m, cab, k < n ? k : n);
}

/* ---------- Una corrida ---------- */
static void corrida(const orden_t *o, reporte_t *r) {
    static uint8_t msg[1024], eco[1024], bloque[512];
    memset(r, 0, sizeof *r);
    int msz = o->msg > (int)sizeof msg ? (int)sizeof msg : o->msg;
    uint64_t suma = 0, maxi = 0;

    if (o->grupo == GRUPO_SIN_TLS) {            /* CONTROL: telemetría en claro por el bus */
        for (int i = 0; i < o->n_msgs; i++) {
            armar_mensaje(msg, msz, o->run_id, i);
            uint64_t t0 = plat_us(); raw_write(msg, msz);
            if (raw_read_exacto(eco, msz) < 0) { r->estado = -1; return; }
            uint64_t d = plat_us() - t0; suma += d; if (d > maxi) maxi = d;
        }
        r->rtt_media = o->n_msgs ? (uint32_t)(suma / o->n_msgs) : 0; r->rtt_max = (uint32_t)maxi;
        return;
    }

    uint32_t heap0 = plat_heap_libre();
    WOLFSSL_CTX *ctx = SSL_CTX_new(wolfTLSv1_3_client_method());
    if (!ctx) { r->estado = -2; return; }
    if (wolfSSL_CTX_load_verify_buffer(ctx, (const unsigned char *)g_ca, g_ca_len, WOLFSSL_FILETYPE_PEM) != WOLFSSL_SUCCESS) {
        r->estado = -3; SSL_CTX_free(ctx); return; }
    SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, NULL);
    WOLFSSL *ssl = SSL_new(ctx);
    if (!ssl) { r->estado = -4; SSL_CTX_free(ctx); return; }
    wolfSSL_SSLSetIORecv(ssl, io_recv); wolfSSL_SSLSetIOSend(ssl, io_send);
    int g = (o->grupo == GRUPO_HIBRIDO) ? GRUPO_TLS_X25519MLKEM768 : GRUPO_TLS_X25519;
    if (wolfSSL_set_groups(ssl, &g, 1) != WOLFSSL_SUCCESS || wolfSSL_UseKeyShare(ssl, (word16)g) != WOLFSSL_SUCCESS) {
        r->estado = -5; goto fin; }

    uint64_t t0 = plat_us();
    int ret = SSL_connect(ssl);
    r->t_hs = (uint32_t)(plat_us() - t0);
    if (ret != WOLFSSL_SUCCESS) { r->estado = (int16_t)cod_error(ssl, ret); goto fin; }
    uint32_t heap1 = plat_heap_libre(); r->heap_usado = heap0 > heap1 ? heap0 - heap1 : 0;

    for (int i = 0; i < o->n_msgs; i++) {               /* telemetría con eco */
        armar_mensaje(msg, msz, o->run_id, i);
        uint64_t a = plat_us();
        int w = SSL_write(ssl, msg, msz);
        if (w != msz) { r->estado = (int16_t)cod_error(ssl, w); goto fin; }
        int k = tls_read_exacto(ssl, eco, msz);
        if (k < 0) { r->estado = (int16_t)k; goto fin; }
        uint64_t d = plat_us() - a; suma += d; if (d > maxi) maxi = d;
    }
    r->rtt_media = o->n_msgs ? (uint32_t)(suma / o->n_msgs) : 0; r->rtt_max = (uint32_t)maxi;

    if (o->bulk > 0) {                                  /* rendimiento: bloque grande */
        memset(bloque, 'B', sizeof bloque);
        uint64_t a = plat_us(); uint32_t env = 0;
        while (env < o->bulk) {
            int n = (o->bulk - env) > sizeof bloque ? (int)sizeof bloque : (int)(o->bulk - env);
            int w = SSL_write(ssl, bloque, n);
            if (w != n) { r->estado = (int16_t)cod_error(ssl, w); goto fin; }
            env += n;
        }
        uint8_t ok[2];
        int k = tls_read_exacto(ssl, ok, 2);
        if (k < 0) { r->estado = (int16_t)k; goto fin; }
        r->bulk_us = (uint32_t)(plat_us() - a);
    }
    SSL_shutdown(ssl);                                  /* envía close_notify */
fin:
    r->stack_libre = plat_stack_libre();
    r->heap_libre = plat_heap_libre();
    SSL_free(ssl); SSL_CTX_free(ctx);
}

void cliente_tls_init(const char *ca_pem, int ca_len) {
    g_ca = ca_pem; g_ca_len = ca_len;
    wolfSSL_Init();
    plat_log("wolfSSL %s (se requiere >= 5.9.4), FRAME_SIZE=%d\n", wolfSSL_lib_version(), FRAME_SIZE);
}

void cliente_tls_bucle(void) {
    orden_t o; reporte_t r;
    for (;;) {
        if (!leer_orden(&o)) { plat_esperar_rx(20); continue; }
        plat_log("START run=%u grupo=%u msg=%u n=%u bulk=%u\n", o.run_id, o.grupo, o.msg, o.n_msgs, (unsigned)o.bulk);
        corrida(&o, &r);
        plat_log("FIN run=%u estado=%d t_hs=%u us\n", o.run_id, r.estado, (unsigned)r.t_hs);
        enviar_reporte(o.run_id, &r);
    }
}
