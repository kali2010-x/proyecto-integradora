/* enlace.h - Capa de enlace confiable sobre I2C, lado ESCLAVO (ESP32).
 * Portable: el mismo código se compila en el ESP32 y en el simulador del PC.
 * Debe coincidir con pi/enlace.py (formato de trama y FRAME_SIZE). */
#ifndef ENLACE_H
#define ENLACE_H
#include <stdint.h>
#include <stddef.h>

#ifndef FRAME_SIZE
#define FRAME_SIZE 128
#endif
#define ENL_HDR 6
#define ENL_CRC 2
#define MAX_PAYLOAD (FRAME_SIZE - ENL_HDR - ENL_CRC)
#define ENL_MAGIC 0xA5
enum { T_POLL = 0, T_DATOS = 1, T_CTRL = 2, T_RESET = 3 };

#define ENL_BUF_TX 8192
#define ENL_BUF_RX 8192

/* Funciones que debe proveer la plataforma (ESP32 o simulador) */
typedef struct {
    void (*lock)(void);
    void (*unlock)(void);
    void (*notificar_rx)(void);        /* llegaron datos/ctrl nuevos para la app */
    void (*notificar_tx)(void);        /* se liberó espacio en el buffer de TX */
    void (*notificar_reset)(void);     /* el maestro pidió RESET */
} enlace_plataforma_t;

uint16_t crc16_ccitt(const uint8_t *d, size_t n);
void enlace_init(const enlace_plataforma_t *p);
void enlace_reset_estado(void);

/* Llamadas desde la tarea del enlace (NO desde la ISR) */
void enlace_procesar_trama_maestro(const uint8_t *trama, size_t len);
void enlace_construir_respuesta(uint8_t out[FRAME_SIZE]);

/* API para la aplicación (cliente TLS) */
int enlace_tx_escribir(const uint8_t *p, int n);      /* devuelve bytes aceptados (0 si lleno) */
int enlace_tx_ctrl(const uint8_t *p, int n);          /* 1 si se encoló, 0 si no hay espacio */
int enlace_rx_leer(uint8_t *p, int n);                /* devuelve bytes leídos (0 si vacío) */
int enlace_ctrl_pop(uint8_t *p, int max);             /* longitud del mensaje o -1 si no hay */
int enlace_tx_vacio(void);

typedef struct {
    uint32_t tramas_rx, tramas_crc_mal, duplicadas, sin_espacio;
} enlace_stats_t;
extern enlace_stats_t enlace_stats;
#endif
