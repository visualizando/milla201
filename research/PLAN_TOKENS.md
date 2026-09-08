# Plan para cuando se renueven los tokens

## Avance del 8 de septiembre de 2026

Acceso verificado. Se calcularon recurrencia por MMSI y año, banderas en los eventos, extremos de gaps dentro del polígono 8466 y presencia mensual en esa ZEE para 2017–agosto de 2026. Se consultaron registros de identidad para los 20 MMSI con más gaps. Resultados, límites y comandos en [FLEET_RESULTS.md](FLEET_RESULTS.md).

Siguen pendientes las trayectorias para contar entradas concretas, la resolución histórica de identidades, ampliar tipos/tamaños al resto de la flota, visitas a puerto y encuentros. La presencia mensual no reemplaza los eventos de entrada y salida. No se ha confirmado ninguna infracción con estos cruces.

## 1. Verificar acceso

- Probar `GFW_API_TOKEN` contra `public-global-vessel-identity:v4.0`.
- Probar un reporte pequeño de enero de 2025 antes de lanzar la descarga completa.
- No guardar el token en Git ni dentro de `docs/`.

## 2. Identidad de los barcos

- Tomar los MMSI que aparecen en los gaps del recorte regional.
- Consultar identidad histórica, no solo el registro actual.
- Guardar nombre, MMSI, IMO, bandera por período, eslora, tonelaje, tipo de barco y arte estimado.
- Marcar cambios de bandera, MMSI o identidad para no contar un mismo barco como varios.

## 3. Permanencia y puertos

- Descargar visitas a puerto y eventos de entrada/salida para esos barcos.
- Construir una tabla por barco: primera entrada, última salida, cantidad de visitas, tiempo entre escalas y puertos más frecuentes.
- Separar puerto de abastecimiento, descarga, espera y cualquier categoría que devuelva GFW.
- No llamar “puerto de abastecimiento” a una visita si la API no informa esa función.

## 4. Tipos y tamaños

- Agrupar gaps por tipo de barco, arte de pesca, rango de eslora y rango de tonelaje.
- Comparar la distribución de la flota con la distribución de los barcos que tienen gaps.
- Calcular tasas dentro de cada grupo solo cuando exista un denominador comparable.

## 5. Otros eventos

- Descargar encuentros entre pesqueros, carriers, apoyo y bunkers.
- Descargar loitering y visitas a puerto.
- Cruzar cada evento con bandera, tipo, tamaño y puerto, manteniendo sus fechas y posiciones.

## 6. ZEE y recorte

- Conseguir un polígono documentado de la ZEE argentina y guardar su versión.
- Mantener el recorte actual como contexto amplio.
- Separar ZEE, mar adyacente y aguas internacionales; no inferir la jurisdicción desde la caja.

## 7. SAR

- Intentar de nuevo `public-global-sar-footprints:v20210924`.
- Si sigue devolviendo 403, usar solo detecciones y porcentaje sin AIS, marcando cobertura desconocida.
- No convertir meses sin registros en cero.

## 8. Salidas del micrositio

- Ranking de banderas.
- Tipos y artes de pesca.
- Tamaño de la flota.
- Permanencia y puertos asociados.
- Encuentros y posibles transbordos.
- Tabla descargable por barco y por año.
- Mantener las horas y días como denominadores técnicos, fuera del centro de la historia.

## 9. Control antes de publicar

- Verificar paginación, fechas, duplicados e identidades vacías.
- Comparar totales mensuales con los reportes anuales.
- Separar cambios de cobertura, proveedor o procesamiento de cambios de comportamiento.
- Escribir resultados descriptivos; los gaps no prueban ilegalidad.
