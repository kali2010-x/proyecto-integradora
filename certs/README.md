# certs/

| Archivo | En el repositorio | Contenido |
|---|---|---|
| `servidor.pem` | Sí | Certificado autofirmado del servidor (ECDSA P-256, CN=servidor-borde, vence el 13/10/2027). El ESP32 lo usa como CA (`cert_servidor.h`). |
| `servidor.key` | **No, nunca** | Clave privada del servidor. Solo existe en la Raspberry Pi y en un respaldo privado. |

Para reproducir el trabajo desde un clon limpio hay dos opciones:

1. **Con la clave original** (solo los autores): copiar `servidor.key` al `certs/` del clon.
2. **Con un par nuevo** (cualquier persona):
   ```bash
   openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes \
       -keyout certs/servidor.key -out certs/servidor.pem -days 365 -subj "/CN=servidor-borde"
   python herramientas/cert_a_header.py      # regenera esp32/firmware/main/cert_servidor.h
   ```
   y volver a compilar y grabar el firmware del ESP32 (el simulador lee el `.pem` directamente).
