/* prueba_enlace.c - Comprueba en el PC las optimizaciones de enlace.c:
 *   1) el CRC por tabla da lo mismo que el CRC bit a bit original;
 *   2) los buffers circulares con memcpy entregan los mismos bytes que un modelo byte a byte.
 * Compilar y ejecutar:  gcc -O2 -Wall -I../esp32/firmware/main prueba_enlace.c -o prueba_enlace && ./prueba_enlace */
#include "../esp32/firmware/main/enlace.c"
#include <stdio.h>
#include <stdlib.h>
#include <time.h>

static uint16_t crc_bit_a_bit(const uint8_t *d, size_t n) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < n; i++) {
        crc ^= (uint16_t)d[i] << 8;
        for (int b = 0; b < 8; b++) crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
    }
    return crc;
}

int main(void) {
    srand(42);
    uint8_t t[FRAME_SIZE];
    /* 1) CRC */
    if (crc16_ccitt((const uint8_t *)"123456789", 9) != 0x29B1) { printf("FALLO: vector de prueba del CRC\n"); return 1; }
    for (int k = 0; k < 200000; k++) {
        size_t n = 1 + (size_t)(rand() % FRAME_SIZE);
        for (size_t i = 0; i < n; i++) t[i] = (uint8_t)rand();
        if (crc16_ccitt(t, n) != crc_bit_a_bit(t, n)) { printf("FALLO: CRC distinto en la prueba %d\n", k); return 1; }
    }
    clock_t a = clock(); volatile uint16_t s = 0;
    for (int k = 0; k < 400000; k++) { t[0] = (uint8_t)k; s ^= crc_bit_a_bit(t, FRAME_SIZE - 2); }
    clock_t b = clock();
    for (int k = 0; k < 400000; k++) { t[0] = (uint8_t)k; s ^= crc16_ccitt(t, FRAME_SIZE - 2); }
    clock_t c = clock();
    printf("CRC: 200 000 tramas aleatorias iguales. Bit a bit %.0f ns/trama; por tabla %.0f ns/trama\n",
           1e9 * (b - a) / CLOCKS_PER_SEC / 400000, 1e9 * (c - b) / CLOCKS_PER_SEC / 400000);
    /* 2) buffer circular frente a un modelo byte a byte */
    static ring_t r; static uint8_t modelo[ENL_BUF_TX]; int m_ini = 0, m_n = 0;
    uint8_t in[600], out[600], esperado[600];
    for (int k = 0; k < 300000; k++) {
        int n = rand() % 600;
        if (rand() & 1) {
            if (n > ring_libre(&r)) n = ring_libre(&r);
            for (int i = 0; i < n; i++) { in[i] = (uint8_t)rand(); modelo[(m_ini + m_n + i) % ENL_BUF_TX] = in[i]; }
            m_n += n; ring_put(&r, in, n);
        } else {
            int e = n > m_n ? m_n : n;
            for (int i = 0; i < e; i++) esperado[i] = modelo[(m_ini + i) % ENL_BUF_TX];
            m_ini = (m_ini + e) % ENL_BUF_TX; m_n -= e;
            int g = ring_get(&r, out, n);
            if (g != e || memcmp(out, esperado, (size_t)e) != 0) { printf("FALLO: buffer circular en la prueba %d\n", k); return 1; }
        }
        if (r.n != m_n) { printf("FALLO: ocupación del buffer en la prueba %d\n", k); return 1; }
    }
    printf("Buffer circular: 300 000 operaciones aleatorias iguales al modelo byte a byte\n");
    printf("TODO CORRECTO\n");
    return 0;
}
