"""Localiza dispositivos Chromecast / Google TV en la red local.

Uso:  uv run buscar [--red 192.168.1.0/24]

Prueba el puerto de Cast (8009) en cada IP de la red en vez de usar mDNS, que no
atraviesa la red NAT de WSL2. El nombre se lee de la API local del dispositivo.
"""
import argparse
import concurrent.futures as cf
import ipaddress
import json
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

from . import config

PUERTO_CAST = 8009


def es_wsl():
    try:
        return "microsoft" in Path("/proc/version").read_text().lower()
    except OSError:
        return False


def ip_local():
    """IP de la red doméstica; en WSL2 la de Windows, no la de la red NAT."""
    if es_wsl():
        try:
            salida = subprocess.run(
                [
                    "powershell.exe", "-NoProfile", "-Command",
                    "(Get-NetIPAddress -AddressFamily IPv4 | "
                    "? {$_.PrefixOrigin -eq 'Dhcp'}).IPAddress",
                ],
                capture_output=True, text=True, timeout=15,
            ).stdout.split()
            if salida:
                return salida[0]
        except (OSError, subprocess.SubprocessError):
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("192.0.2.1", 9))  # no envía nada; solo elige la interfaz
        return s.getsockname()[0]


def puerto_abierto(ip):
    try:
        with socket.create_connection((str(ip), PUERTO_CAST), timeout=0.7):
            return True
    except OSError:
        return False


def nombre(ip):
    url = f"http://{ip}:8008/setup/eureka_info?params=name"
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return json.load(r).get("name") or "(sin nombre)"
    except (OSError, ValueError):
        return "(sin nombre)"


def buscar(red):
    hosts = list(red.hosts())
    with cf.ThreadPoolExecutor(128) as ex:
        abiertos = [ip for ip, ok in zip(hosts, ex.map(puerto_abierto, hosts)) if ok]
        nombres = list(ex.map(nombre, abiertos))
    return [(str(ip), n) for ip, n in zip(abiertos, nombres)]


def main():
    ap = argparse.ArgumentParser(description="Busca dispositivos Cast en la red local.")
    ap.add_argument("--red", help="red a recorrer, p. ej. 192.168.1.0/24 (por defecto, la tuya /24)")
    args = ap.parse_args()

    red = ipaddress.ip_network(args.red or f"{ip_local()}/24", strict=False)
    print(f"Buscando dispositivos Cast en {red}…")
    encontrados = buscar(red)
    if not encontrados:
        sys.exit("No se encontró ninguno. ¿Está encendida la tele? Prueba con --red.")

    actual = config.ip_destino()
    print()
    print(f"  #  {'IP':<16} Nombre")
    for i, (ip, n) in enumerate(encontrados, 1):
        marca = "  ← destino actual" if ip == actual else ""
        print(f"  {i}  {ip:<16} {n}{marca}")
    print()

    if not sys.stdin.isatty():
        return
    eleccion = input(f"¿Cuál guardo como destino en {config.RUTA.name}? [número, Intro = ninguno]: ").strip()
    if not eleccion:
        return
    try:
        ip, n = encontrados[int(eleccion) - 1]
    except (ValueError, IndexError):
        sys.exit("Número no válido; no se ha cambiado nada.")
    config.guardar_destino(ip, n)
    print(f"Guardado: {n} ({ip}) en {config.RUTA}")


if __name__ == "__main__":
    main()
