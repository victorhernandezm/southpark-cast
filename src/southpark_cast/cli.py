"""Proyecta un episodio de southpark.lat en el Google TV.

Uso:  uv run proyectar URL_DEL_EPISODIO [--tv IP]

yt-dlp extrae la lista HLS maestra (vídeo y audio separados) y se envía tal
cual al receptor multimedia del Google TV, que elige la calidad por sí mismo.
Se conecta por IP directa al puerto 8009, así que funciona desde WSL2 sin mDNS.
"""
import argparse
import os
import select
import sys
import termios
import time
import tty
import uuid

import pychromecast
import yt_dlp

TV_POR_DEFECTO = "192.168.1.5"  # «Entrada»


def extraer(url):
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    if info.get("_type") == "playlist":  # por si la página trae varias partes
        info = info["entries"][0]
    manifiesto = next(
        (f["manifest_url"] for f in info["formats"] if f.get("manifest_url")), None
    )
    if not manifiesto:
        sys.exit("No se encontró una lista HLS en la página.")
    return info.get("title") or "South Park", info.get("thumbnail"), manifiesto


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--tv", default=TV_POR_DEFECTO, help="IP del Google TV")
    args = ap.parse_args()

    print("Extrayendo vídeo…")
    titulo, miniatura, manifiesto = extraer(args.url)
    print(f"  {titulo}")

    print(f"Conectando con {args.tv}…")
    cc = pychromecast.get_chromecast_from_host((args.tv, 8009, uuid.uuid4(), None, None))
    cc.wait(timeout=15)
    if cc.app_id:  # si hay otra app abierta (p. ej. Spotify) no se abre el receptor
        cc.quit_app()
        time.sleep(3)
    mc = cc.media_controller
    mc.play_media(
        manifiesto,
        "application/x-mpegURL",
        title=titulo,
        thumb=miniatura,
        stream_type="BUFFERED",
    )
    mc.block_until_active(timeout=20)

    for _ in range(30):  # espera a que empiece a reproducir
        mc.update_status()
        time.sleep(1)
        estado = mc.status.player_state
        if estado in ("PLAYING", "BUFFERING"):
            break
        if estado == "IDLE" and mc.status.idle_reason == "ERROR":
            sys.exit("El Google TV no pudo reproducir el vídeo.")

    # El receptor de Google se cierra si queda en pausa sin ningún emisor
    # conectado, así que el script sigue conectado hasta que acabe el episodio.
    mando(cc, mc)
    cc.disconnect()


def fmt(seg):
    seg = int(seg or 0)
    return f"{seg // 3600}:{seg % 3600 // 60:02d}:{seg % 60:02d}"


def mando(cc, mc):
    print(
        "\nMando:  espacio pausa/sigue · ←/→ ±10 s · ⇧←/⇧→ (o a/d) ±60 s"
        " · ↑/↓ volumen · q parar y salir\n"
        "Deja esta ventana abierta mientras ves el episodio.\n"
    )
    fd = sys.stdin.fileno()
    viejo = termios.tcgetattr(fd)
    tty.setcbreak(fd)
    try:
        ultimo = 0
        while True:
            if select.select([sys.stdin], [], [], 0.5)[0]:
                tecla = os.read(fd, 16).decode(errors="ignore")
                ahora = mc.status.adjusted_current_time or 0
                if tecla == " ":
                    mc.pause() if mc.status.player_state == "PLAYING" else mc.play()
                elif tecla in ("\x1b[C", "\x1b[D"):
                    mc.seek(max(0, ahora + (10 if tecla == "\x1b[C" else -10)))
                elif tecla in ("\x1b[1;2C", "d", "\x1b[1;2D", "a"):
                    mc.seek(max(0, ahora + (60 if tecla in ("\x1b[1;2C", "d") else -60)))
                elif tecla in ("\x1b[A", "\x1b[B"):
                    vol = cc.status.volume_level + (0.05 if tecla == "\x1b[A" else -0.05)
                    cc.set_volume(min(1.0, max(0.0, vol)))
                elif tecla.lower() == "q":
                    mc.stop()
                    break
            if time.time() - ultimo > 1:
                ultimo = time.time()
                if not cc.app_id:  # la cerraron desde el mando de la tele
                    print("\nEl Google TV cerró el vídeo.")
                    break
                s = mc.status
                if s.player_state == "IDLE" and s.idle_reason in ("FINISHED", "ERROR"):
                    print(f"\nFin ({s.idle_reason.lower()}).")
                    break
                vol = round((cc.status.volume_level or 0) * 100) if cc.status else 0
                print(
                    f"\r{s.player_state or '':<10} {fmt(s.adjusted_current_time)}"
                    f" / {fmt(s.duration)}   vol {vol:3d}%   ",
                    end="",
                    flush=True,
                )
    except KeyboardInterrupt:
        mc.stop()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, viejo)
        print()


if __name__ == "__main__":
    main()
