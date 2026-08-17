"""Da de alta o cambia la contrasena de las cuentas del panel.

Se ejecuta a mano:  python3 crear_usuario_panel.py

Pide las contrasenas sin mostrarlas, las convierte en hash y actualiza el .env
local. Al final imprime las variables tal cual hay que pegarlas en Render, donde
no existe el .env y se cargan a mano en el panel de entorno.

La contrasena nunca se guarda ni se muestra: del .env solo sale su hash, que no
se puede revertir.
"""
import getpass
import pathlib
import re
import sys

from werkzeug.security import generate_password_hash

LARGO_MINIMO = 8
RUTA_ENV = pathlib.Path(__file__).parent / ".env"


def pedir_contrasena(usuario):
    """Pide la contrasena dos veces y comprueba que sea utilizable."""
    while True:
        print(f"\n--- Contraseña para {usuario} ---")
        print("  (no vas a ver nada mientras escribes, es normal)")

        primera = getpass.getpass("  Contraseña: ")

        if not primera.strip():
            print("  ERROR: quedó vacía. Escribe algo y pulsa Enter.")
            continue
        if len(primera) < LARGO_MINIMO:
            print(f"  ERROR: usa al menos {LARGO_MINIMO} caracteres. "
                  "El panel queda expuesto en internet.")
            continue

        segunda = getpass.getpass("  Repítela para confirmar: ")
        if primera != segunda:
            print("  ERROR: no coinciden. Empezamos de nuevo.")
            continue

        return primera


def escribir_en_env(variables):
    """Actualiza el .env conservando el resto del archivo tal cual estaba."""
    if not RUTA_ENV.exists():
        print(f"\nNo encuentro {RUTA_ENV}. Copia las lineas de abajo a mano.")
        return False

    texto = RUTA_ENV.read_text()

    for clave, valor in variables.items():
        linea = f"{clave}={valor}"
        texto, cambios = re.subn(rf"^{clave}=.*$", lambda _m: linea,
                                 texto, count=1, flags=re.M)
        if not cambios:
            texto = texto.rstrip("\n") + "\n" + linea + "\n"

    # Respaldo antes de tocar nada, por si algo sale mal.
    (RUTA_ENV.parent / ".env.respaldo").write_text(RUTA_ENV.read_text())
    RUTA_ENV.write_text(texto)
    return True


def main():
    print("=" * 58)
    print("  Cuentas de acceso al panel de life")
    print("=" * 58)

    cuentas = [("Gabriel", "", ), ("Alex", "_2")]
    variables = {}

    for usuario, sufijo in cuentas:
        contrasena = pedir_contrasena(usuario)
        variables[f"ADMIN_USER{sufijo}"] = usuario
        variables[f"ADMIN_PASSWORD_HASH{sufijo}"] = generate_password_hash(contrasena)

    if escribir_en_env(variables):
        print(f"\nListo: {RUTA_ENV.name} actualizado "
              "(respaldo en .env.respaldo).")
        print("Reinicia uvicorn y entra con tu usuario y tu contraseña.")

    print("\n" + "=" * 58)
    print("  Para Render: pega estas variables en Environment")
    print("=" * 58)
    for clave, valor in variables.items():
        print(f"{clave}={valor}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nCancelado, no se cambió nada.")
