/* main.c - Plataforma ESP32: I2C esclavo (driver v2), línea READY y tareas.
 * ESP-IDF v5.5 con CONFIG_I2C_ENABLE_SLAVE_DRIVER_VERSION_2=y.
 *
 * Conexiones (ESP32 DevKit clásico):
 *   GPIO21 = SDA  -> Raspberry GPIO4 (pin 7)   [pull-up 4,7 kΩ a 3,3 V]
 *   GPIO22 = SCL  -> Raspberry GPIO5 (pin 29)  [pull-up 4,7 kΩ a 3,3 V]
 *   GPIO4  = READY-> Raspberry GPIO17 (pin 11)
 *   GND           -> Raspberry GND (pin 9)
 *   Alimentación: cable USB a un puerto USB de la Raspberry (queda dentro de la medición del INA219). */
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "freertos/queue.h"
#include "freertos/semphr.h"
#include "driver/i2c_slave.h"
#include "driver/gpio.h"
#include "esp_timer.h"
#include "esp_system.h"
#include "esp_log.h"
#include "enlace.h"
#include "plataforma.h"
#include "cliente_tls.h"
#if !MODO_ECO
#include "cert_servidor.h"      /* generado con herramientas/cert_a_header.py */
#endif

#define PIN_SDA    21
#define PIN_SCL    22
#define PIN_READY  4
#define DIR_I2C    0x28

static const char *TAG = "nodo";
typedef struct { uint8_t d[FRAME_SIZE]; uint32_t n; } trama_t;
static QueueHandle_t cola_rx;
static i2c_slave_dev_handle_t h_i2c;
static SemaphoreHandle_t mtx, sem_evento;
static volatile uint32_t tramas_eco;

/* ---------- Funciones de plataforma usadas por enlace.c y cliente_tls.c ---------- */
static void lk(void) { xSemaphoreTake(mtx, portMAX_DELAY); }
static void ulk(void) { xSemaphoreGive(mtx); }
static void notificar(void) { xSemaphoreGive(sem_evento); }
static void esperar(int ms) { TickType_t t = pdMS_TO_TICKS(ms); xSemaphoreTake(sem_evento, t ? t : 1); }
uint64_t plat_us(void) { return (uint64_t)esp_timer_get_time(); }
void plat_esperar_rx(int ms) { esperar(ms); }
void plat_esperar_tx(int ms) { esperar(ms); }
uint32_t plat_heap_libre(void) { return esp_get_free_heap_size(); }
uint32_t plat_stack_libre(void) { return (uint32_t)uxTaskGetStackHighWaterMark(NULL); } /* bytes en ESP-IDF */
void plat_log(const char *fmt, ...) { va_list a; va_start(a, fmt); vprintf(fmt, a); va_end(a); }

/* ---------- Callback de la ISR: el maestro terminó de escribir una trama ---------- */
static bool on_receive(i2c_slave_dev_handle_t s, const i2c_slave_rx_done_event_data_t *ev, void *arg) {
    (void)s; (void)arg;
    BaseType_t despertar = pdFALSE;
    trama_t t;
    gpio_set_level(PIN_READY, 0);                       /* la respuesta anterior ya no vale */
    t.n = ev->length > FRAME_SIZE ? FRAME_SIZE : ev->length;
    memcpy(t.d, ev->buffer, t.n);
    xQueueSendFromISR(cola_rx, &t, &despertar);
    return despertar == pdTRUE;
}

/* ---------- Tarea del enlace: procesa la trama y deja lista la respuesta ---------- */
static void tarea_enlace(void *arg) {
    (void)arg;
    trama_t t; uint8_t resp[FRAME_SIZE]; uint32_t escritos;
    for (;;) {
        if (xQueueReceive(cola_rx, &t, portMAX_DELAY) != pdTRUE) continue;
#if MODO_ECO
        memcpy(resp, t.d, FRAME_SIZE);                  /* eco: devuelve la misma trama */
        tramas_eco++;
#else
        enlace_procesar_trama_maestro(t.d, t.n);
        enlace_construir_respuesta(resp);
#endif
        if (i2c_slave_write(h_i2c, resp, FRAME_SIZE, &escritos, 100) != ESP_OK || escritos != FRAME_SIZE)
            ESP_LOGW(TAG, "i2c_slave_write incompleto (%u)", (unsigned)escritos);
        gpio_set_level(PIN_READY, 1);                   /* avisa al maestro: puede leer */
    }
}

#if !MODO_ECO
static void tarea_tls(void *arg) {
    (void)arg;
    cliente_tls_init(CERT_SERVIDOR_PEM, (int)strlen(CERT_SERVIDOR_PEM));
    cliente_tls_bucle();
}
#endif

void app_main(void) {
    gpio_config_t g = { .pin_bit_mask = 1ULL << PIN_READY, .mode = GPIO_MODE_OUTPUT };
    gpio_config(&g);
    gpio_set_level(PIN_READY, 0);

    mtx = xSemaphoreCreateMutex();
    sem_evento = xSemaphoreCreateBinary();
    cola_rx = xQueueCreate(4, sizeof(trama_t));
    enlace_plataforma_t p = { lk, ulk, notificar, notificar, notificar };
    enlace_init(&p);

    i2c_slave_config_t cfg = {
        .i2c_port = 0,
        .sda_io_num = PIN_SDA,
        .scl_io_num = PIN_SCL,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .send_buf_depth = 4 * FRAME_SIZE,
        .receive_buf_depth = 2 * FRAME_SIZE,
        .slave_addr = DIR_I2C,
        .addr_bit_len = I2C_ADDR_BIT_LEN_7,
    };
    ESP_ERROR_CHECK(i2c_new_slave_device(&cfg, &h_i2c));
    i2c_slave_event_callbacks_t cbs = { .on_receive = on_receive, .on_request = NULL };
    ESP_ERROR_CHECK(i2c_slave_register_event_callbacks(h_i2c, &cbs, NULL));

    xTaskCreatePinnedToCore(tarea_enlace, "enlace", 4096, NULL, 10, NULL, 0);
#if MODO_ECO
    ESP_LOGI(TAG, "MODO ECO listo. Direccion 0x%02X, trama %d bytes", DIR_I2C, FRAME_SIZE);
    for (;;) { vTaskDelay(pdMS_TO_TICKS(5000)); ESP_LOGI(TAG, "tramas eco: %u", (unsigned)tramas_eco); }
#else
    xTaskCreatePinnedToCore(tarea_tls, "tls", 32768, NULL, 5, NULL, 1);
    ESP_LOGI(TAG, "Nodo TLS listo. Direccion 0x%02X, trama %d bytes", DIR_I2C, FRAME_SIZE);
#endif
}
