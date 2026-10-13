"""
buscar_marcador_analizador.py - Semana 8: busca el texto de la telemetría en una captura del analizador lógico.

En PulseView: agregar el decodificador I2C sobre la captura, luego clic derecho en la fila del
decodificador -> "Export all annotations" (o "Export annotations for this row") -> archivo .txt.
También sirve la salida de sigrok-cli:  sigrok-cli -i captura.sr -P i2c > anotaciones.txt

  python3 herramientas/buscar_marcador_analizador.py anotaciones.txt
"""
import re, sys

MARCADOR = b"TELEMETRIA"
patron = re.compile(r"Data (read|write)[:\s]+([0-9A-Fa-f]{2})\b")
escritos, leidos = bytearray(), bytearray()
for linea in open(sys.argv[1], encoding="utf-8", errors="ignore"):
    m = patron.search(linea)
    if m:
        (leidos if m.group(1) == "read" else escritos).append(int(m.group(2), 16))
print(f"Bytes decodificados: {len(escritos)} escritos (Raspberry->ESP32), {len(leidos)} leídos (ESP32->Raspberry)")
for nombre, datos in (("Raspberry->ESP32", escritos), ("ESP32->Raspberry", leidos)):
    i = datos.find(MARCADOR)
    if i >= 0:
        print(f"  [{nombre}] MARCADOR VISIBLE en el bus: ...{bytes(datos[i:i+40])!r}...")
    else:
        print(f"  [{nombre}] marcador NO encontrado (datos cifrados o ausentes)")
