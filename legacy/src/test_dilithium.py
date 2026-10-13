import oqs

ALGORITMO = "ML-DSA-65"

with oqs.Signature(ALGORITMO) as firmante:
    pub = firmante.generate_keypair()
    mensaje = b"Prueba Dilithium"
    firma = firmante.sign(mensaje)
    print(f"✅ Firma generada: {len(firma)} bytes")

with oqs.Signature(ALGORITMO) as verificador:
    valida = verificador.verify(mensaje, firma, pub)
    print(f"✅ Verificación: {valida}")

