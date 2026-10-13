/* plataforma.h - Funciones que cada plataforma (ESP32 o simulador) implementa. */
#ifndef PLATAFORMA_H
#define PLATAFORMA_H
#include <stdint.h>
uint64_t plat_us(void);                 /* reloj monotónico en microsegundos */
void plat_esperar_rx(int ms);           /* bloquea hasta que llegue algo o pase ms */
void plat_esperar_tx(int ms);           /* bloquea hasta que haya espacio/ACK o pase ms */
uint32_t plat_heap_libre(void);         /* heap libre actual (0 si no aplica) */
uint32_t plat_stack_libre(void);        /* mínimo de pila libre de la tarea (0 si no aplica) */
void plat_log(const char *fmt, ...);
#endif
