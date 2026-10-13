#!/usr/bin/env python3
"""
Script de lectura del sensor INA219.
Lee voltaje, corriente y potencia cada segundo y los guarda en un CSV.
"""

import time
import csv
from datetime import datetime
from pathlib import Path

import board
import busio
from adafruit_ina219 import INA219


# -------- Configuración --------
INTERVALO_SEGUNDOS = 1          # Lectura cada 1 segundo
DURACION_SEGUNDOS = 600         # 600 s = 10 minutos
ARCHIVO_CSV = Path("../data/ina219_reposo_10min.csv")


def main():
    # Crear bus I2C y conectar al sensor
    i2c = busio.I2C(board.SCL, board.SDA)
    ina = INA219(i2c)

    # Crear carpeta de datos si no existe
    ARCHIVO_CSV.parent.mkdir(parents=True, exist_ok=True)

    # Abrir CSV y escribir encabezados
    with ARCHIVO_CSV.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "voltaje_V", "corriente_mA", "potencia_mW"])

        print(f"Iniciando captura de {DURACION_SEGUNDOS} s...")
        print(f"Archivo: {ARCHIVO_CSV}")
        print("Presiona Ctrl+C para detener antes de tiempo.\n")

        inicio = time.monotonic()
        try:
            while time.monotonic() - inicio < DURACION_SEGUNDOS:
                timestamp = datetime.now().isoformat(timespec="milliseconds")

                # Lecturas del sensor
                voltaje_V = ina.bus_voltage          # Voltaje del bus (V)
                corriente_mA = ina.current           # Corriente (mA)

                # Potencia calculada correctamente: V × mA = mW
                potencia_mW = voltaje_V * corriente_mA

                writer.writerow([
                    timestamp,
                    f"{voltaje_V:.3f}",
                    f"{corriente_mA:.3f}",
                    f"{potencia_mW:.3f}",
                ])
                f.flush()  # Escribir al disco inmediatamente

                print(f"{timestamp}  {voltaje_V:6.3f} V  "
                      f"{corriente_mA:8.3f} mA  {potencia_mW:8.3f} mW")

                time.sleep(INTERVALO_SEGUNDOS)

        except KeyboardInterrupt:
            print("\nCaptura interrumpida por el usuario.")

    print(f"\nListo. Datos guardados en: {ARCHIVO_CSV}")


if __name__ == "__main__":
    main()
