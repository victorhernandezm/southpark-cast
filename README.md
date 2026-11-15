# southpark-cast

Proyecta episodios de [southpark.lat](https://www.southpark.lat) en un Google TV
(o cualquier dispositivo Chromecast) de la red local, y hace de mando a distancia
desde la terminal.

## Instalación

```sh
uv sync
```

## Elegir el dispositivo de destino

```sh
uv run buscar                         # lista los dispositivos Cast por IP y nombre
uv run buscar --red 192.168.0.0/24    # si tu red no es la que detecta
```

```
  #  IP               Nombre
  1  192.168.1.5      Entrada  ← destino actual
```

Al final pregunta cuál guardar como destino y lo escribe en `config.toml` (no se
sube a git). También puedes crearlo a mano a partir de `config.example.toml`:

```toml
[destino]
ip = "192.168.1.5"
```

`buscar` prueba el puerto de Cast (8009) en cada IP de la red en vez de usar mDNS,
porque mDNS no funciona desde WSL2. En WSL2 toma la red de Windows.

## Uso

```sh
uv run proyectar "https://www.southpark.lat/episodios/..."
uv run proyectar "https://..." --tv 192.168.1.7   # otro dispositivo, puntualmente
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
