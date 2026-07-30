"""Punto de entrada para despliegue con uvicorn (servidor ASGI de produccion).

Flask es WSGI, no ASGI, asi que se envuelve con asgiref.WsgiToAsgi para que
uvicorn pueda servirlo directamente. Esto reemplaza al servidor de desarrollo
de Flask (run.py) para un despliegue real.

Uso:
    uvicorn main:app --host 0.0.0.0 --port 8000
"""
from asgiref.wsgi import WsgiToAsgi
from dotenv import load_dotenv

load_dotenv()

from app import create_app  # noqa: E402 (debe ir despues de load_dotenv)

flask_app = create_app()
app = WsgiToAsgi(flask_app)
