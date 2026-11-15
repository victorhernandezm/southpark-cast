# southpark-cast

Proyecta episodios de [southpark.lat](https://www.southpark.lat) en un Google TV
(o cualquier dispositivo con Chromecast) de tu red local, y convierte la terminal
en el mando a distancia.

```
$ uv run proyectar "https://www.southpark.lat/episodios/yy0vjs/south-park-especial-pandemia-temporada-24-ep-1"
Extrayendo vídeo…
  Especial Pandemia
Conectando con 192.168.1.5…

Mando:  espacio pausa/sigue · ←/→ ±10 s · ⇧←/⇧→ (o a/d) ±60 s · ↑/↓ volumen · q parar y salir
Deja esta ventana abierta mientras ves el episodio.

PLAYING    0:00:35 / 0:47:20   vol 100%
```

## Requisitos

- [uv](https://docs.astral.sh/uv/) (instala Python 3.12 por su cuenta si hace falta).
- Linux, macOS o WSL2. El mando usa `termios`, así que no funciona en el Python
  nativo de Windows; en Windows, usa WSL.
- Un Google TV, Chromecast o tele con Chromecast integrado en la misma red que el
  ordenador.

## Instalación

```sh
git clone https://github.com/victorhernandezm/southpark-cast.git
cd southpark-cast
uv sync
```

`uv sync` crea el entorno virtual `.venv/` con las dependencias exactas de
`uv.lock` y registra los comandos `buscar` y `proyectar`.

## Inicio rápido

```sh
uv run buscar                                      # 1. localiza la tele y guárdala como destino
uv run proyectar "https://www.southpark.lat/..."   # 2. proyecta un episodio
```

## `buscar`: localizar dispositivos

Lista los dispositivos Cast de la red con su IP y su nombre, y te deja guardar uno
como destino.

```
$ uv run buscar
Buscando dispositivos Cast en 192.168.1.0/24…

  #  IP               Nombre
  1  192.168.1.5      Entrada  ← destino actual
  2  192.168.1.23     Dormitorio

¿Cuál guardo como destino en config.toml? [número, Intro = ninguno]: 1
Guardado: Entrada (192.168.1.5) en /…/southpark-cast/config.toml
```

| Opción | Descripción |
|---|---|
| `--red CIDR` | Red que se recorre, p. ej. `192.168.0.0/24`. Por defecto es la `/24` de tu IP. |

- No usa la búsqueda automática (mDNS): prueba el puerto de Cast (8009) en cada
  IP de la red. Así funciona también desde WSL2, donde mDNS no llega a la red de
  casa.
- En WSL2 detecta la red de Windows (la IP obtenida por DHCP), no la red interna
  de WSL.
- Si lo ejecutas sin terminal interactiva (por ejemplo, redirigiendo la salida),
  solo lista los dispositivos y no pregunta.

## `proyectar`: enviar un episodio

```sh
uv run proyectar URL_DEL_EPISODIO [--tv IP]
```

| Opción | Descripción |
|---|---|
| `URL_DEL_EPISODIO` | Página del episodio en southpark.lat. |
| `--tv IP` | Envía a ese dispositivo solo esta vez, sin tocar `config.toml`. |

Si la tele tiene otra app abierta (Spotify, YouTube…), `proyectar` la cierra antes
de abrir el reproductor.

### Mando

| Tecla | Acción |
|---|---|
| espacio | pausa / sigue |
| ← / → | retrocede / avanza 10 s |
| a / d (o Mayús + ← / →) | retrocede / avanza 60 s |
| ↑ / ↓ | sube / baja el volumen un 5 % |
| q (o Ctrl+C) | para el vídeo y sale |

La línea de estado muestra el estado, la posición, la duración y el volumen. El
script termina solo cuando acaba el episodio o si cierras el vídeo desde la tele.

> **Deja la terminal abierta** mientras ves el episodio. El receptor de vídeo de
> Google se cierra si queda en pausa sin ningún dispositivo conectado.

## Configuración

El destino se guarda en `config.toml`, en la raíz del proyecto. Lo crea `buscar`;
también puedes copiar `config.example.toml` y editarlo:

```toml
[destino]
ip = "192.168.1.5"
nombre = "Entrada"  # solo informativo
```

- `config.toml` está en `.gitignore`: cada máquina tiene el suyo.
- Para usar otro fichero, pon su ruta en la variable `SOUTHPARK_CAST_CONFIG`:

  ```sh
  SOUTHPARK_CAST_CONFIG=~/salon.toml uv run proyectar "https://…"
  ```

- Prioridad de la IP: `--tv` › `config.toml`. Si no hay ninguna, `proyectar` te
  indica que ejecutes `buscar`.

## Solución de problemas

| Síntoma | Causa y solución |
|---|---|
| `buscar` no encuentra nada | La tele está apagada o en otra red, o la red detectada no es la correcta. Prueba con `--red`. |
| `proyectar` no conecta | La tele cambió de IP. Vuelve a ejecutar `buscar` y, para evitarlo, resérvale la IP en el router. |
| El vídeo se cierra al pausar | La terminal de `proyectar` se cerró. Déjala abierta durante el episodio. |
| «No se encontró una lista HLS» | La página cambió o no es un episodio. Actualiza `yt-dlp` con `uv lock --upgrade-package yt-dlp && uv sync`. |
| La tele muestra un error | El enlace del vídeo caduca. Vuelve a lanzar `proyectar`, que pide uno nuevo. |

## Cómo funciona

1. `yt-dlp` extrae de la página la lista HLS maestra del CDN de Paramount. Vídeo
   y audio vienen en pistas separadas, así que se envía la lista completa en vez
   de un fichero suelto; por eso `catt cast` no sirve con esta web.
2. `pychromecast` se conecta a la tele por IP directa (puerto 8009), abre el
   *Default Media Receiver* y le pasa la lista. La tele elige la calidad (hasta
   1080p) y descarga el vídeo directamente: el ordenador solo hace de mando.
3. El script sigue conectado durante la reproducción para enviar las órdenes del
   mando y para que el receptor no se cierre al pausar.

## Estructura

```
src/southpark_cast/
├── cli.py      # proyectar: extracción, envío y mando
├── buscar.py   # buscar: recorre la red y lista dispositivos
└── config.py   # lectura y escritura de config.toml
config.example.toml
```

## Limitaciones

- El audio y los subtítulos son los que ofrece la web.
- Solo se ha probado con southpark.lat. Otras páginas que `yt-dlp` reconozca y
  sirvan HLS sin DRM probablemente funcionen, pero no está garantizado.
