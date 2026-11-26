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
/* Optimización: los buffers circulares copian por bloques con memcpy (como máximo dos tramos)
 * en lugar de byte a byte con una operación de módulo por cada byte. */
static void ring_put(ring_t *r, const uint8_t *p, int n) {
    int fin = (r->ini + r->n) % (int)sizeof(r->d);
    int a = (int)sizeof(r->d) - fin; if (a > n) a = n;
    memcpy(r->d + fin, p, (size_t)a);
    memcpy(r->d, p + a, (size_t)(n - a));
    r->n += n;
}
static int ring_get(ring_t *r, uint8_t *p, int n) {
    if (n > r->n) n = r->n;
    int a = (int)sizeof(r->d) - r->ini; if (a > n) a = n;
    memcpy(p, r->d + r->ini, (size_t)a);
    memcpy(p + a, r->d, (size_t)(n - a));
    r->ini = (r->ini + n) % (int)sizeof(r->d); r->n -= n;
    return n;
}

/* Optimización: CRC-16/CCITT-FALSE por tabla. El vector global constante de 256 entradas (512 bytes
 * de flash) reemplaza el lazo de 8 iteraciones por bit: una consulta por byte en lugar de ocho
 * desplazamientos condicionales. Da el mismo resultado que la versión bit a bit
 * (herramientas/verificar_optimizaciones.py lo comprueba). */
static const uint16_t CRC_TABLA[256] = {
    0x0000, 0x1021, 0x2042, 0x3063, 0x4084, 0x50A5, 0x60C6, 0x70E7,
    0x8108, 0x9129, 0xA14A, 0xB16B, 0xC18C, 0xD1AD, 0xE1CE, 0xF1EF,
    0x1231, 0x0210, 0x3273, 0x2252, 0x52B5, 0x4294, 0x72F7, 0x62D6,
    0x9339, 0x8318, 0xB37B, 0xA35A, 0xD3BD, 0xC39C, 0xF3FF, 0xE3DE,
    0x2462, 0x3443, 0x0420, 0x1401, 0x64E6, 0x74C7, 0x44A4, 0x5485,
    0xA56A, 0xB54B, 0x8528, 0x9509, 0xE5EE, 0xF5CF, 0xC5AC, 0xD58D,
    0x3653, 0x2672, 0x1611, 0x0630, 0x76D7, 0x66F6, 0x5695, 0x46B4,
    0xB75B, 0xA77A, 0x9719, 0x8738, 0xF7DF, 0xE7FE, 0xD79D, 0xC7BC,
    0x48C4, 0x58E5, 0x6886, 0x78A7, 0x0840, 0x1861, 0x2802, 0x3823,
    0xC9CC, 0xD9ED, 0xE98E, 0xF9AF, 0x8948, 0x9969, 0xA90A, 0xB92B,
    0x5AF5, 0x4AD4, 0x7AB7, 0x6A96, 0x1A71, 0x0A50, 0x3A33, 0x2A12,
    0xDBFD, 0xCBDC, 0xFBBF, 0xEB9E, 0x9B79, 0x8B58, 0xBB3B, 0xAB1A,
    0x6CA6, 0x7C87, 0x4CE4, 0x5CC5, 0x2C22, 0x3C03, 0x0C60, 0x1C41,
    0xEDAE, 0xFD8F, 0xCDEC, 0xDDCD, 0xAD2A, 0xBD0B, 0x8D68, 0x9D49,
    0x7E97, 0x6EB6, 0x5ED5, 0x4EF4, 0x3E13, 0x2E32, 0x1E51, 0x0E70,
    0xFF9F, 0xEFBE, 0xDFDD, 0xCFFC, 0xBF1B, 0xAF3A, 0x9F59, 0x8F78,
    0x9188, 0x81A9, 0xB1CA, 0xA1EB, 0xD10C, 0xC12D, 0xF14E, 0xE16F,
    0x1080, 0x00A1, 0x30C2, 0x20E3, 0x5004, 0x4025, 0x7046, 0x6067,
    0x83B9, 0x9398, 0xA3FB, 0xB3DA, 0xC33D, 0xD31C, 0xE37F, 0xF35E,
    0x02B1, 0x1290, 0x22F3, 0x32D2, 0x4235, 0x5214, 0x6277, 0x7256,
    0xB5EA, 0xA5CB, 0x95A8, 0x8589, 0xF56E, 0xE54F, 0xD52C, 0xC50D,
    0x34E2, 0x24C3, 0x14A0, 0x0481, 0x7466, 0x6447, 0x5424, 0x4405,
    0xA7DB, 0xB7FA, 0x8799, 0x97B8, 0xE75F, 0xF77E, 0xC71D, 0xD73C,
    0x26D3, 0x36F2, 0x0691, 0x16B0, 0x6657, 0x7676, 0x4615, 0x5634,
    0xD94C, 0xC96D, 0xF90E, 0xE92F, 0x99C8, 0x89E9, 0xB98A, 0xA9AB,
    0x5844, 0x4865, 0x7806, 0x6827, 0x18C0, 0x08E1, 0x3882, 0x28A3,
    0xCB7D, 0xDB5C, 0xEB3F, 0xFB1E, 0x8BF9, 0x9BD8, 0xABBB, 0xBB9A,
    0x4A75, 0x5A54, 0x6A37, 0x7A16, 0x0AF1, 0x1AD0, 0x2AB3, 0x3A92,
    0xFD2E, 0xED0F, 0xDD6C, 0xCD4D, 0xBDAA, 0xAD8B, 0x9DE8, 0x8DC9,
    0x7C26, 0x6C07, 0x5C64, 0x4C45, 0x3CA2, 0x2C83, 0x1CE0, 0x0CC1,
    0xEF1F, 0xFF3E, 0xCF5D, 0xDF7C, 0xAF9B, 0xBFBA, 0x8FD9, 0x9FF8,
    0x6E17, 0x7E36, 0x4E55, 0x5E74, 0x2E93, 0x3EB2, 0x0ED1, 0x1EF0,
};

uint16_t crc16_ccitt(const uint8_t *d, size_t n) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < n; i++) crc = (uint16_t)((crc << 8) ^ CRC_TABLA[(crc >> 8) ^ d[i]]);
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
