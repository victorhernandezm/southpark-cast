"""Configuración del dispositivo de destino (config.toml en la raíz del proyecto)."""
import os
import tomllib
from pathlib import Path

RUTA = Path(
    os.environ.get("SOUTHPARK_CAST_CONFIG")
    or Path(__file__).resolve().parents[2] / "config.toml"
)


def leer():
    if not RUTA.exists():
        return {}
    with RUTA.open("rb") as f:
        return tomllib.load(f)


def ip_destino():
    return leer().get("destino", {}).get("ip")


def guardar_destino(ip, nombre):
    nombre = nombre.replace("\\", "\\\\").replace('"', '\\"')
    RUTA.write_text(
        "# Dispositivo al que «proyectar» envía el vídeo.\n"
        "# Genera este fichero con «uv run buscar» o edítalo a mano.\n\n"
        "[destino]\n"
        f'ip = "{ip}"\n'
        f'nombre = "{nombre}"  # solo informativo\n',
        encoding="utf-8",
    )
