# southpark-cast

Proyecta episodios de [southpark.lat](https://www.southpark.lat) en un Google TV
(o cualquier dispositivo Chromecast) de la red local, y hace de mando a distancia
desde la terminal.

## Instalación

```sh
uv sync
```

## Uso

```sh
uv run proyectar "https://www.southpark.lat/episodios/..."
uv run proyectar "https://..." --tv 192.168.1.5   # otra IP
```

| Tecla | Acción |
|---|---|
| espacio | pausa / sigue |
| ← / → | ±10 s |
| a / d (o Mayús+←/→) | ±60 s |
| ↑ / ↓ | volumen |
| q | parar y salir |

Deja la terminal abierta mientras ves el episodio: el receptor de vídeo de Google
se cierra si queda en pausa sin ningún dispositivo conectado.

## Cómo funciona

- `yt-dlp` extrae de la página la lista HLS maestra. Vídeo y audio vienen por
  separado, así que se envía la lista completa en vez de un fichero suelto (por
  eso `catt cast` no sirve aquí).
- `pychromecast` abre el Default Media Receiver en la tele y le pasa la lista; la
  tele descarga el vídeo directamente del CDN de Paramount.
- La conexión es por IP directa al puerto 8009, sin búsqueda mDNS, así que
  funciona desde WSL2 en modo NAT. Conviene reservar la IP de la tele en el router.
