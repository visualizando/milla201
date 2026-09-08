# Actividad, frecuencia y detecciones SAR

Estado al 8 de septiembre de 2026: token validado. Reportes reales de esfuerzo, presencia de pesqueros y SAR descargados con resolución mensual. Usar `download_context_annual.py` para descargar los diez años con menos solicitudes. Los totales del mes de prueba se comparan contra el bloque anual. La capa oficial de huellas SAR `public-global-sar-footprints:v20210924` devuelve HTTP 403, «Not authorized by permissions». La corrección por cobertura sigue bloqueada; no se publica una densidad estimada.

## Ejecutar

Desde la raíz del proyecto:

```
python scripts/download_context.py --start 2025-01 --end 2025-01
python scripts/download_context_annual.py
python scripts/analyze_context.py
python -m unittest discover -s scripts -p test_context.py
```

Primero validar un mes: forma de la respuesta, filtro de pesqueros, identidad MMSI, ausencia de paginación y sumas. El descargador detiene errores y no reemplaza reportes faltantes por ceros. Conserva consultas, fecha de descarga y hash junto a cada respuesta. No envía consultas concurrentes: GFW permite un reporte a la vez por usuario. Las respuestas con timeout requieren revisar last-report antes de reintentar.

## Definiciones

- Misma caja exploratoria que los gaps: 70–40° O, 60–30° S. No es la ZEE argentina.
- 116 meses completos, enero de 2017 a agosto de 2026. No comparar 2026 parcial con años enteros.
- Horas de pesca aparente: suma de Fishing Effort v4.0. No equivalen a capturas.
- Presencia: Presence v4.0 filtrada a pesqueros, agrupada por MMSI. Filtro y agrupación verificados con el reporte real de enero de 2025. Hay filas sin MMSI: sus horas se conservan en los totales de actividad, pero se excluyen de las tasas y del conteo de MMSI distintos.
- Días-barco equivalentes observados = horas de presencia / 24. No son días calendario únicos con al menos una señal ni tiempo real total en el mar.
- Tasa de gaps = gaps de los MMSI presentes en ambas bases / días-barco equivalentes observados × 1.000. Conservar aparte los gaps y MMSI sin cruce.
- Porcentaje de flota con gaps = MMSI de la intersección / MMSI distintos con presencia × 100.
- Al agregar varios meses, volver a contar MMSI distintos sobre la unión: no sumar barcos mensuales. Agregar numeradores y denominadores antes de dividir; no promediar tasas mensuales.
- SAR: detecciones totales y sin coincidencia AIS, y porcentaje sin coincidencia. Incluye barcos de distintos tipos; no asumir que todo objeto sin AIS es pesquero ni infractor.
- La proporción SAR sin AIS describe las detecciones realizadas, no una tasa corregida por cobertura.

## Cobertura SAR pendiente de obtener

GFW ofrece huellas de detección en WKT en el portal de descargas. Se necesitan las escenas realmente procesadas (incluidas las que tuvieron cero detecciones), recortar cada huella a la caja y sumar superficie observada por pasada. Usar el catálogo general de Sentinel-1 como si fuera el de GFW introduciría escenas no procesadas. No se calcula densidad corregida sin este dato.

Para comparar períodos: detecciones por km²-pasada, número de escenas, área única observada, distribución espacial de pasadas y análisis restringido a celdas con cobertura común. Los conteos por sí solos no separan más barcos de más imágenes.

## Cambios de fuente a considerar

GFW documenta una transición de proveedor AIS el 22 de abril de 2026 y cambios de cobertura. No trasladar el porcentaje global de cambio a Argentina sin medirlo en la zona. También documenta una modificación de la máscara océano/tierra de SAR desde el 28 de marzo de 2026. Separar resultados antes/después de estos cambios y evitar atribuir automáticamente la variación a comportamiento pesquero.

## Fuentes consultadas el 7 de septiembre de 2026

- https://globalfishingwatch.org/our-apis/documentation/docs/v3/4wings
- https://globalfishingwatch.org/our-apis/documentation/docs/v3/4wings/report
- https://api-doc.globalfishingwatch.org/our-apis/documentation/docs/v3/4wings/last-report
- https://globalfishingwatch.org/platform-update/2024-may-data-download-portal-new-dataset-released-featuring-vessel-detections-from-sentinel-1-sar/
- https://globalfishingwatch.org/platform-update/update-in-our-synthetic-aperture-radar-sar-data-pipeline/
- https://globalfishingwatch.org/platform-update/data-vendor-transition/

## Qué se publica

Tres series mensuales: horas de pesca aparente, gaps por 1.000 días-barco observados, y porcentaje de detecciones SAR sin coincidencia AIS. También se exportan presencia, MMSI distintos, intersección de barcos, horas sin MMSI y comparaciones anuales y enero–agosto. Para SAR se agrega enero–junio de 2025 y 2026. Los meses sin registros SAR se marcan como cobertura desconocida y no se convierten en ceros. La interfaz avisa que SAR incluye barcos no pesqueros y que faltan las huellas.

### Procedencia

Respuestas anuales originales: `data/raw/context_annual/`, con consulta, fecha y SHA-256. Archivos mensuales derivados: `data/raw/context/`, con referencia al bloque anual. Solo los indicadores agregados llegan a `docs/data`. El token permanece en `.secrets/gfw.env`.
