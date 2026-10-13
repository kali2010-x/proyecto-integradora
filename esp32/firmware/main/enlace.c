/* enlace.c - Implementación portable del esclavo del enlace I2C. */
#include "enlace.h"
#include <string.h>

enlace_stats_t enlace_stats;
static enlace_plataforma_t P;

/* --- buffers circulares --- */
typedef struct { uint8_t d[ENL_BUF_TX]; int ini, n; } ring_t;
static ring_t tx, rx;                       /* tx: app->maestro ; rx: maestro->app */
static uint8_t ctrl_tx[4][MAX_PAYLOAD]; static int ctrl_tx_len[4], ctrl_tx_n, ctrl_tx_ini;
static uint8_t ctrl_rx[4][MAX_PAYLOAD]; static int ctrl_rx_len[4], ctrl_rx_n, ctrl_rx_ini;

/* --- estado ARQ --- */
static uint8_t seq_tx, ultima_seq_rx;
static int pend_activa; static uint8_t pend_tipo, pend_seq, pend_len, pend_p[MAX_PAYLOAD];

static uint8_t sig(uint8_t s) { return s >= 255 ? 1 : s + 1; }
static int ring_libre(ring_t *r) { return (int)sizeof(r->d) - r->n; }
static void ring_put(ring_t *r, const uint8_t *p, int n) {
    for (int i = 0; i < n; i++) r->d[(r->ini + r->n + i) % sizeof(r->d)] = p[i];
    r->n += n;
}
static int ring_get(ring_t *r, uint8_t *p, int n) {
    if (n > r->n) n = r->n;
    for (int i = 0; i < n; i++) p[i] = r->d[(r->ini + i) % sizeof(r->d)];
    r->ini = (r->ini + n) % sizeof(r->d); r->n -= n;
    return n;
}

uint16_t crc16_ccitt(const uint8_t *d, size_t n) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < n; i++) {
        crc ^= (uint16_t)d[i] << 8;
        for (int b = 0; b < 8; b++) crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
    }
    return crc;
}

void enlace_reset_estado(void) {
    tx.ini = tx.n = 0; rx.ini = rx.n = 0;
    ctrl_tx_n = ctrl_tx_ini = 0; ctrl_rx_n = ctrl_rx_ini = 0;
    seq_tx = 0; ultima_seq_rx = 0; pend_activa = 0;
}

void enlace_init(const enlace_plataforma_t *p) {
    P = *p; memset(&enlace_stats, 0, sizeof enlace_stats); enlace_reset_estado();
}

void enlace_procesar_trama_maestro(const uint8_t *t, size_t len) {
    int notif_rx = 0, notif_tx = 0, notif_reset = 0;
    P.lock();
    enlace_stats.tramas_rx++;
    if (len != FRAME_SIZE || t[0] != ENL_MAGIC ||
        crc16_ccitt(t, FRAME_SIZE - 2) != (uint16_t)((t[FRAME_SIZE - 2] << 8) | t[FRAME_SIZE - 1])) {
        enlace_stats.tramas_crc_mal++;
        P.unlock(); return;                    /* se responde con el estado anterior */
    }
    uint8_t tipo = t[1], seq = t[2], ack = t[3];
    int n = (t[4] << 8) | t[5];
    if (n > MAX_PAYLOAD) { enlace_stats.tramas_crc_mal++; P.unlock(); return; }
    if (tipo == T_RESET) {
        enlace_reset_estado(); notif_reset = 1;
        P.unlock(); if (notif_reset && P.notificar_reset) P.notificar_reset(); return;
    }
    if (pend_activa && ack == pend_seq) { pend_activa = 0; notif_tx = 1; }
    if ((tipo == T_DATOS || tipo == T_CTRL)) {
        if (seq == sig(ultima_seq_rx)) {
            if (tipo == T_DATOS) {
                if (ring_libre(&rx) >= n) { ring_put(&rx, t + ENL_HDR, n); ultima_seq_rx = seq; notif_rx = 1; }
                else enlace_stats.sin_espacio++;      /* no se confirma: el maestro reintentará */
            } else if (ctrl_rx_n < 4) {
                int k = (ctrl_rx_ini + ctrl_rx_n) % 4;
                memcpy(ctrl_rx[k], t + ENL_HDR, n); ctrl_rx_len[k] = n; ctrl_rx_n++;
                ultima_seq_rx = seq; notif_rx = 1;
            } else enlace_stats.sin_espacio++;
        } else enlace_stats.duplicadas++;
    }
    P.unlock();
    if (notif_rx && P.notificar_rx) P.notificar_rx();
    if (notif_tx && P.notificar_tx) P.notificar_tx();
}

void enlace_construir_respuesta(uint8_t out[FRAME_SIZE]) {
    P.lock();
    if (!pend_activa) {                         /* preparar nueva trama si hay algo que enviar */
        if (ctrl_tx_n > 0) {                    /* el control tiene prioridad */
            pend_tipo = T_CTRL; pend_len = (uint8_t)ctrl_tx_len[ctrl_tx_ini];
            memcpy(pend_p, ctrl_tx[ctrl_tx_ini], pend_len);
            ctrl_tx_ini = (ctrl_tx_ini + 1) % 4; ctrl_tx_n--;
            seq_tx = sig(seq_tx); pend_seq = seq_tx; pend_activa = 1;
        } else if (tx.n > 0) {
            pend_tipo = T_DATOS; pend_len = (uint8_t)ring_get(&tx, pend_p, MAX_PAYLOAD);
            seq_tx = sig(seq_tx); pend_seq = seq_tx; pend_activa = 1;
        }
    }
    memset(out, 0, FRAME_SIZE);
    out[0] = ENL_MAGIC; out[3] = ultima_seq_rx;
    if (pend_activa) {
        out[1] = pend_tipo; out[2] = pend_seq; out[4] = 0; out[5] = pend_len;
        memcpy(out + ENL_HDR, pend_p, pend_len);
    } else {
        out[1] = T_POLL; out[2] = seq_tx;
    }
    P.unlock();
    uint16_t c = crc16_ccitt(out, FRAME_SIZE - 2);
    out[FRAME_SIZE - 2] = (uint8_t)(c >> 8); out[FRAME_SIZE - 1] = (uint8_t)c;
}

int enlace_tx_escribir(const uint8_t *p, int n) {
    P.lock(); int libre = ring_libre(&tx); if (n > libre) n = libre; ring_put(&tx, p, n); P.unlock();
    return n;
}
int enlace_tx_ctrl(const uint8_t *p, int n) {
    if (n > MAX_PAYLOAD) return 0;
    P.lock(); int ok = 0;
    if (ctrl_tx_n < 4) { int k = (ctrl_tx_ini + ctrl_tx_n) % 4; memcpy(ctrl_tx[k], p, n); ctrl_tx_len[k] = n; ctrl_tx_n++; ok = 1; }
    P.unlock(); return ok;
}
int enlace_rx_leer(uint8_t *p, int n) { P.lock(); n = ring_get(&rx, p, n); P.unlock(); return n; }
int enlace_ctrl_pop(uint8_t *p, int max) {
    P.lock(); int n = -1;
    if (ctrl_rx_n > 0) { n = ctrl_rx_len[ctrl_rx_ini]; if (n > max) n = max; memcpy(p, ctrl_rx[ctrl_rx_ini], n);
        ctrl_rx_ini = (ctrl_rx_ini + 1) % 4; ctrl_rx_n--; }
    P.unlock(); return n;
}
int enlace_tx_vacio(void) { P.lock(); int v = (tx.n == 0 && !pend_activa && ctrl_tx_n == 0); P.unlock(); return v; }
