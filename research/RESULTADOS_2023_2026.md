# Resultados de la descarga GFW

Instantánea descargada el 7 de septiembre de 2026, dataset `public-global-gaps-events:v4.0`, barcos `FISHING`, intervalo solicitado [2023-01-01, 2026-09-08). Todas las páginas de las 45 ventanas mensuales se recuperaron; no se guardó el token en los entregables.

## Archivos para Observable

- `datos_2023_2026/ais_disabling_events.csv`: **79.102** eventos con inicio desde 2023, para reemplazar el adjunto del mismo nombre. Conserva sus 15 columnas y el orden original.
- `atlantico_sudoccidental/ais_disabling_events.csv`: **3.854** eventos cuyo inicio cae entre 70° y 40° O, 60° y 30° S. La caja no equivale a la ZEE argentina.
- `observable_evolucion_gaps.js`: copiar en una nueva celda JavaScript. Selector de área, línea mensual, tabla y comparación enero–agosto de 2026 con 2023.
- `gaps_mensuales.csv`, `gaps_anuales.csv`: conteos agregados para reutilizar.
- `evolucion_gaps.png` y `.svg`: gráfico de la serie mensual.

No se modificó el notebook remoto. Reemplazar su archivo adjunto por el CSV global mantiene tanto sus mapas globales como regionales disponibles.

## Qué muestran los datos

| Período | Global | Atlántico sudoccidental |
|---|---:|---:|
| 2023 completo | 28.143 | 1.235 |
| 2024 completo | 24.125 | 995 |
| 2025 completo | 18.124 | 843 |
| Enero–agosto 2023 | 18.536 | 1.015 |
| Enero–agosto 2024 | 16.843 | 716 |
| Enero–agosto 2025 | 12.684 | 642 |
| Enero–agosto 2026 | 8.683 | 773 |

En el recorte regional, 2025 presenta **31,7% menos eventos que 2023**. En cambio, enero–agosto de 2026 presenta **20,4% más que enero–agosto de 2025**, aunque sigue 23,8% por debajo de los mismos meses de 2023. Son cambios de conteos detectados, no una tasa de ilegalidad ni un resultado causal.

El último inicio observado es **2026-09-03 05:42:13 UTC** y el último final **2026-09-03 21:27:42 UTC**. Septiembre es parcial y queda fuera de los gráficos y comparaciones anuales. La descarga completa de páginas no certifica que el prototipo GFW sea exhaustivo o que los últimos meses no vayan a revisarse.

## Auditoría

La respuesta contiene **79.509 IDs únicos** de eventos que se solapan con el intervalo. De ellos, **407** comenzaron antes de 2023: permanecen en `events_normalized.csv`, pero se excluyen del CSV del mapa y los conteos temporales. No hay IDs duplicados en el CSV final. La bandera falta en 11.698 de los 79.509 eventos normalizados. Todos incluyen fechas, coordenadas OFF/ON, duración y MMSI. Clase de arte, eslora y tonelaje permanecen vacíos porque Events no los ofrece.

Se preservan **3.189 gaps de más de 30 días** entre los eventos iniciados desde 2023; el más largo dura unas 31.809 horas. No se eliminan silenciosamente. Esta cola hace que las horas totales de silencio sean especialmente sensibles a eventos extremos; el gráfico principal cuenta eventos, no horas.

Para afirmar que la situación mejoró haría falta considerar cambios de flota y de observación, y construir un denominador de exposición consistente. La selección es por comienzo del gap; no reconstruye la trayectoria durante el silencio ni prueba que el barco pescó dentro de la ZEE.

Fuente y método: [GFW Events](https://globalfishingwatch.org/our-apis/documentation/docs/v3/events/get-all-events), [datasets y versiones](https://globalfishingwatch.org/our-apis/documentation/docs/v3/general-api-doc/key-concepts), [limitaciones de AIS-off](https://globalfishingwatch.org/our-apis/documentation/docs/v3/general-api-doc/data-caveats).
