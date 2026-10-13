#ifndef CLIENTE_TLS_H
#define CLIENTE_TLS_H
/* Grupos de intercambio de claves (deben coincidir con pi/servidor_tls.py) */
enum { GRUPO_CLASICO = 0, GRUPO_HIBRIDO = 1, GRUPO_SIN_TLS = 2 };
void cliente_tls_init(const char *ca_pem, int ca_len);
void cliente_tls_bucle(void);   /* nunca retorna: espera órdenes START del maestro */
#endif
