# Serie completa desde 2017

Descarga autenticada de GFW v4.0, barcos FISHING, entre 2017-01-01 y 2026-09-08 (exclusivo). Último inicio observado: 3 de septiembre de 2026. No se incluyeron credenciales.

- `ais_disabling_events.csv`: 222.463 eventos únicos desde 2017, con las 15 columnas originales para reemplazar el adjunto de Observable.
- `ais_disabling_events_atlantico.csv`: 18.897 eventos iniciados en la caja 70°–40° O, 60°–30° S. Si se usa este archivo como adjunto, renombrarlo `ais_disabling_events.csv`; los mapas globales también quedarían limitados a esa selección.
- `events_normalized.csv`: columnas adicionales, ID GFW y metadatos.
- `gaps_mensuales.csv`: conteos globales y regionales por mes; septiembre de 2026 está señalado como parcial.
- `gaps_anuales.csv`: 2017–2025 completos; 2026 incluye solo lo observado hasta septiembre y está señalado como parcial.
- `evolucion_gaps_desde_2017.png` / `.svg`: serie hasta agosto de 2026, con línea en 2020-01-01.

El archivo original de Welch tenía inicios de eventos entre 2017-01-01 00:20:33 UTC y 2019-12-31 06:54:12 UTC. La marca en 2020 señala el fin de ese período, no un cambio de método en la serie nueva. Toda la nueva serie proviene de v4.0 y puede diferir del archivo original incluso dentro de 2017–2019.

Se recuperaron 72 ventanas mensuales para 2017–2022 y se combinaron con las 45 ventanas ya descargadas desde 2023. Los eventos repetidos se unieron por ID, conservando la representación descargada más recientemente. La descarga completa no certifica exhaustividad de detección de la fuente.

Las dos celdas de `../celdas_desde_2017.md` se ejecutaron con los datos reales a 375 y 928 px. Producen 116 meses, enero de 2017 a agosto de 2026, y 18.889 eventos regionales en ese período; los 8 restantes del CSV regional son de septiembre y no se dibujan. No se modificó el notebook remoto.
