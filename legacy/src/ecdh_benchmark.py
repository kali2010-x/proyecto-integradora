from cryptography.hazmat.primitives.asymmetric import ec
import time
import csv
import datetime
import os

CURVA = ec.SECP256R1()          # curva congelada: P-256
NOMBRE_ALGORITMO = "ECDH-P256"  # etiqueta que irá al CSV
REPETICIONES = 100
CALENTAMIENTO = 10
RUTA_CSV = "../data/ecdh_piloto.csv"


def una_ronda():
    """Ejecuta 2 KeyGen + 2 Agreement y devuelve las 4 duraciones
    junto con si ambos secretos coinciden."""
    resultados = []

    # --- KeyGen_A ---
    t0 = time.perf_counter_ns()
    clave_a = ec.generate_private_key(CURVA)
    t1 = time.perf_counter_ns()

    # --- KeyGen_B ---
    t2 = time.perf_counter_ns()
    clave_b = ec.generate_private_key(CURVA)
    t3 = time.perf_counter_ns()

    # --- Agreement_A (A usa la pública de B) ---
    t4 = time.perf_counter_ns()
    secreto_a = clave_a.exchange(ec.ECDH(), clave_b.public_key())
    t5 = time.perf_counter_ns()

    # --- Agreement_B (B usa la pública de A) ---
    t6 = time.perf_counter_ns()
    secreto_b = clave_b.exchange(ec.ECDH(), clave_a.public_key())
    t7 = time.perf_counter_ns()

    coincide = (secreto_a == secreto_b)

    resultados.append(("KeyGen_A", t1 - t0))
    resultados.append(("KeyGen_B", t3 - t2))
    resultados.append(("Agreement_A", t5 - t4))
    resultados.append(("Agreement_B", t7 - t6))
    return resultados, coincide


def main():
    os.makedirs(os.path.dirname(RUTA_CSV), exist_ok=True)

    with open(RUTA_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["run_id", "algoritmo", "operacion",
                         "duracion_ns", "timestamp", "secretos_coinciden"])

        # Fase de calentamiento (se descarta)
        print(f"Calentando ({CALENTAMIENTO} rondas descartadas)...")
        for _ in range(CALENTAMIENTO):
            una_ronda()

        # 100 repeticiones reales
        print(f"Midiendo {REPETICIONES} repeticiones...")
        fallos = 0
        for i in range(1, REPETICIONES + 1):
            resultados, coincide = una_ronda()
            if not coincide:
                fallos += 1
            ts = datetime.datetime.now().isoformat()
            for operacion, duracion in resultados:
                writer.writerow([i, NOMBRE_ALGORITMO, operacion,
                                 duracion, ts, coincide])

    print(f"Listo. CSV en {RUTA_CSV}")
    print(f"Fallos de coincidencia: {fallos} (debe ser 0)")


if __name__ == "__main__":
    main()
