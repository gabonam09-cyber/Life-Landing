import os

from dotenv import load_dotenv

load_dotenv()  # carga .env antes de leer cualquier configuracion

from app import create_app  # noqa: E402 (debe ir despues de load_dotenv)

app = create_app()

if __name__ == "__main__":
    debug = os.environ.get("FLASK_ENV", "production").lower() == "development"
    port = int(os.environ.get("PORT", 5000))
    app.run(host="127.0.0.1", port=port, debug=debug)
