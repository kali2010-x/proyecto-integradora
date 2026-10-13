from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
pub = priv.public_key()
mensaje = b"Prueba RSA"

firma = priv.sign(
    mensaje,
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256()
)
print(f"✅ Firma RSA: {len(firma)} bytes")

pub.verify(
    firma, mensaje,
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
    hashes.SHA256()
)
print("✅ Verificación RSA OK")
