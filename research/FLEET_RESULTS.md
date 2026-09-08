# Barcos que se repiten · 8 de septiembre de 2026

## Qué calculamos

Los 18.897 gaps del recorte regional corresponden a 1.342 MMSI. De ellos, 821 tienen gaps en más de un año: reúnen 17.425 eventos (92,2%). Los 20 con más eventos reúnen 4.330 (22,9%). Es una concentración retrospectiva, no una tasa de riesgo ajustada por actividad.

En 2025, 194 de los 259 MMSI con gaps habían aparecido en algún año anterior (74,9%); 109 habían aparecido en 2024. Son dos definiciones distintas de recurrencia. La serie empieza en 2017, por lo que “primera vez” no implica primer arribo. En 2026 hay 202 recurrentes sobre 222 hasta el 3 de septiembre; no comparar esa fracción como un año completo ni como evidencia causal.

| Nombre más frecuente en eventos | MMSI | Bandera en gaps | Gaps | Años con gaps |
|---|---|---|---:|---:|
| PLAYA PESMAR UNO | 224369000 | ESP | 322 | 9 |
| PLAYA DA CATIVA | 224004000 | ESP | 318 | 10 |
| LU QING-YUAN YU 209 | 412329691 | CHN | 293 | 7 |
| LU QING YUAN YU 205 | 412329686 | CHN | 277 | 5 |
| PLAYA PESMAR DOS | 224770000 | ESP | 267 | 10 |

Por bandera del evento: CHN 8.555; ESP 3.453; ARG 2.199; KOR 1.554; TWN 918. No dividir por una flota de otra cobertura ni atribuir la bandera a la propiedad.

## Cruce geográfico

Fuente: `public-eez-areas/context-layers/8466`, Marine Regions distribuido por GFW. Guardamos el GeoJSON completo y su SHA-256 en el resultado. La API identifica el polígono como “Argentinian Exclusive Economic Zone”; su metadata no explicita una versión histórica de la geometría. Usamos el polígono recuperado el 8/9/2026 para todos los años, sin simplificar. No reconstruimos cambios de jurisdicción ni toda la posición territorial argentina respecto de espacios disputados.

2.375 eventos tienen al menos un extremo dentro: 2.116 con bandera ARG, 247 con otras banderas conocidas y 12 sin bandera. Contamos cada evento una sola vez aunque ambos extremos estén dentro. Los puntos sobre el borde se incluyen. No interpolamos el recorrido durante el gap. No llamamos a estos eventos “incursiones” ni “pesca ilegal”.

También descargamos diez reportes de Presence v4.0, pesqueros, agrupados por MMSI, resolución mensual y espacial HIGH, agregados dentro de la región 8466. Cubren enero de 2017 a agosto de 2026. Hay 1.533 MMSI en estos reportes, de los cuales 921 también tienen gaps en el recorte regional en algún momento de la serie. Esta coincidencia no exige simultaneidad y no demuestra que el gap ocurriera dentro.

PLAYA PESMAR DOS aparece con presencia en 43 meses repartidos en diez años; PLAYA PESMAR UNO en 47 meses de nueve años. Son meses con registros, no 43 o 47 entradas ni estancias continuas. El agregado espacial puede incluir celdas que tocan el borde; hay que revisar puntos y trayectorias antes de afirmar cruces.

Los casos uruguayos requieren revisar la Zona Común de Pesca Argentino-Uruguaya. Presencia de otra bandera tampoco distingue tránsito de pesca ni verifica permisos.

## Identidades, tipos y tamaños

Consultamos `public-global-vessel-identity:v4.0` para los 20 MMSI con más gaps. Guardamos todos los resultados completos sin elegir automáticamente una identidad. Los campos de arte, eslora e IMO del CSV son conjuntos de candidatos de registro con coincidencia exacta de MMSI, no una atribución histórica definitiva.

Por ejemplo, la consulta de 224369000 devuelve tres entradas y varios vessel ID; sus eventos usan PLAYA PESMAR UNO y PP1. Hay un candidato de registro con IMO 9281877, arrastre y 71 m. No unimos automáticamente distintos MMSI por nombre. `412329689` incluye una variante de nombre que corresponde a “205”, además de “208”: queda visible en los alias para revisión.

## Reproducir

Instalar `requirements-fleet.txt`. Ejecutar desde el repositorio:

```powershell
python scripts/download_eez.py
python scripts/analyze_fleet.py --events data/raw/gfw_2017_2022/events_normalized.csv data/raw/gfw_2023_2026/events_normalized.csv
python scripts/download_fleet_identity.py
python scripts/enrich_fleet.py
python scripts/test_fleet.py
python scripts/build_site.py
```

La geometría se obtiene mediante GET autenticado a `https://gateway.api.globalfishingwatch.org/v3/datasets/public-eez-areas/context-layers/8466`. Se conserva en `data/raw/fleet/eez_region.json`. El token se lee de `.secrets/gfw.env`; no se envía al navegador. Las descargas son secuenciales y se reanudan desde caché con hashes.

## Qué falta para hablar de entradas concretas y abastecimiento

1. Descargar o acceder a trayectorias de los candidatos, revisar posiciones a ambos lados del borde, errores AIS y tolerancia espacial. La presencia mensual no permite contar entradas.
2. Cruzar actividad aparente y permisos históricos, además de las zonas del tratado argentino-uruguayo. No inferir autorización desde bandera.
3. Resolver identidades históricas por IMO, MMSI, nombre, señal distintiva y fechas, marcando casos ambiguos.
4. Obtener visitas a puerto y encuentros. Una escala no demuestra abastecimiento; no están calculados en esta entrega.
5. Ampliar tipos/tamaños a toda la flota con denominadores comparables. La muestra de 20 no representa a toda la flota.

Fuentes: [flujo oficial de análisis por ZEE](https://globalfishingwatch.org/our-apis/documentation/docs/api-workflows/monitoring-trawlers-in-an-eez), [limitaciones GFW](https://api-doc.globalfishingwatch.org/our-apis/documentation/docs/v3/general-api-doc/data-caveats), [CTMFM](https://ctmfm.org/estadistica-pesquera/).
