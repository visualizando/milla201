# Milla 201

Investigación visual sobre gaps AIS y pesca alrededor de Argentina, 2017–2026. Sitio estático en GitHub Pages; datos GFW v4.0. No implica afiliación con The Washington Post ni con GFW.

## Carpetas

```
.secrets/        token local, ignorado por Git
data/raw/       páginas originales GFW, ignoradas (copias locales)
data/interim/   intercambios temporales, ignorados
data/processed/ CSV y JSON generados, ignorados
scripts/        descarga, normalización, combinación y preparación
site/           HTML, CSS, JavaScript y bibliotecas del sitio
docs/           versión pública compilada para GitHub Pages
research/       metodología, procedencia y próximos cruces
```

## Uso local

Python 3.10+. No se requieren paquetes Python para datos ni compilación.

1. Guardar el token en `.secrets/gfw.env` siguiendo `.env.example`, o usar la variable de entorno `GFW_API_TOKEN`. Nunca ponerlo en `site/`, `docs/` o una URL. El sitio no usa API autenticada.
2. `python scripts/download.py --start 2017-01-01 --end 2026-09-08 --out data/raw/gfw_full`
3. `python scripts/prepare_data.py --source data/raw/gfw_full/ais_disabling_events.csv`
4. `python scripts/build_site.py`
5. `python -m http.server 8000 --directory docs` y abrir http://localhost:8000.

La instantánea inicial proviene de dos descargas ya realizadas, en `data/raw/gfw_2017_2022` y `data/raw/gfw_2023_2026`. El CSV unificado local está en `data/interim/ais_disabling_events.csv`. Se puede regenerar con `python scripts/combine_downloads.py --inputs data/raw/gfw_2017_2022 data/raw/gfw_2023_2026 --out data/interim/combined --start 2017-01-01 --end 2026-09-08`.

## Publicación

GitHub Pages sirve `main:/docs`. Tras cambiar fuentes o datos, ejecutar `build_site.py`, revisar el resultado, hacer commit y push de `site/`, scripts y `docs/`. Solo una lista explícita de datos derivados se copia a docs; nunca se copia data/raw o .secrets.

Los CSV del mapa tienen 15 columnas compatibles con el notebook original. Se incluyen como descarga global comprimida y CSV regional. La página carga un JSON reducido, no el CSV global completo.

## Alcance

Esta edición tiene resultados reales de gaps. Presence, Fishing Effort y SAR están presentados como cruces pendientes, no resultados. La región es una caja, no una ZEE. Toda la serie usa v4.0; no mezcla el archivo histórico de Welch con años recientes. Los conteos de 2026 y el mapa incluyen hasta septiembre 3; las curvas y comparaciones temporales excluyen septiembre por ser parcial.

Referencias y limitaciones están en el sitio y en `research/`. La versión del algoritmo no fija una instantánea inmutable: por eso se conservan páginas y fechas de recuperación.
