# ---- Parámetros del experimento (deben coincidir con la Raspberry) ----
set(FRAME_SIZE 128)   # tamaño de trama del enlace: 32, 64 o 128 (prueba de eco, semanas 3-4)
set(MODO_ECO 0)       # 1 = firmware de prueba de eco (semanas 3-4); 0 = cliente TLS

set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DWOLFSSL_USER_SETTINGS")
idf_component_register(SRCS "main.c" "enlace.c" "cliente_tls.c"
                       INCLUDE_DIRS "."
                       PRIV_REQUIRES wolfssl esp_driver_i2c esp_driver_gpio esp_timer)
target_compile_definitions(${COMPONENT_LIB} PRIVATE FRAME_SIZE=${FRAME_SIZE} MODO_ECO=${MODO_ECO})
