import oqs
import time
import csv
import datetime
import os

ALGORITMO = "ML-KEM-768"      # nombre exacto confirmado en el paso 1
REPETICIONES = 100
CALENTAMIENTO = 10
RUTA_CSV = "../data/kyber_piloto.csv"


def una_ronda():
    """Ejecuta KeyGen + Encaps + Decaps UNA vez y devuelve
    las 3 duraciones y si los secretos coinciden."""
    resultados = []

    # --- Receptor (Bob) genera su par de claves ---
    with oqs.KeyEncapsulation(ALGORITMO) as receptor:
        t0 = time.perf_counter_ns()
        pub = receptor.generate_keypair()
        t1 = time.perf_counter_ns()

        # --- Emisor (Alice) encapsula usando la clave pública de Bob ---
        with oqs.KeyEncapsulation(ALGORITMO) as emisor:
            t2 = time.perf_counter_ns()
            texto_cifrado, secreto_emisor = emisor.encap_secret(pub)
            t3 = time.perf_counter_ns()

        # --- Receptor decapsula para recuperar el secreto ---
        t4 = time.perf_counter_ns()
        secreto_receptor = receptor.decap_secret(texto_cifrado)
        t5 = time.perf_counter_ns()

    coincide = (secreto_emisor == secreto_receptor)

    resultados.append(("KeyGen", t1 - t0))
    resultados.append(("Encaps", t3 - t2))
    resultados.append(("Decaps", t5 - t4))
    return resultados, coincide


def main():
    # Asegurar que la carpeta data exista
    os.makedirs(os.path.dirname(RUTA_CSV), exist_ok=True)

    with open(RUTA_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["run_id", "algoritmo", "operacion",
                         "duracion_ns", "timestamp", "secretos_coinciden"])

        # --- Fase de calentamiento (se descarta) ---
        print(f"Calentando ({CALENTAMIENTO} rondas descartadas)...")
        for _ in range(CALENTAMIENTO):
            una_ronda()

        # --- 100 repeticiones reales ---
        print(f"Midiendo {REPETICIONES} repeticiones...")
        fallos = 0
        for i in range(1, REPETICIONES + 1):
            resultados, coincide = una_ronda()
            if not coincide:
                fallos += 1
            ts = datetime.datetime.now().isoformat()
            for operacion, duracion in resultados:
                writer.writerow([i, ALGORITMO, operacion,
                                 duracion, ts, coincide])

    print(f"Listo. CSV en {RUTA_CSV}")
    print(f"Fallos de coincidencia: {fallos} (debe ser 0)")


if __name__ == "__main__":
    main()
