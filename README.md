| Файл | Размер | Источник |
|---|---|---|
| `moscow_districts.csv` | 7K | Справочник 108 районов Москвы (mos.ru + Kaggle: Administrative divisions of Moscow) |
| `moscow_districts.geojson` | 1.1M | Russia_geojson_OSM (GitHub: timurkanaz), OpenStreetMap |
| `instagram_real_dataset.csv` | 60K | chinmai-gudivada/Instagram-Data-Analytics — 119 реальных постов |
| `competitor_reels.csv` | 1K | Публичные метрики Instagram-аккаунтов в нише подарков |
| `smm_channels.csv` | 1K | Сводка бенчмарков рекламных площадок |
| `hh_vacancies_moscow.csv` | 700K | Mendeley vacancies (575 957 строк → 4 815 по Москве и нашим позициям) с индексацией зарплат к 2026 году |
| `kaggle_social_media_ads.csv` | 40M | Kaggle: jsonk11/social-media-advertising-dataset — 300 000 рекламных кампаний |
| `kaggle_marketing_campaigns.csv` | 27M | Kaggle: manishabhatt22/marketing-campaign-performance-dataset — 200 000 кампаний |
| `mendeley_vacancies_moscow.csv` | ~1M | Промежуточный экстракт Mendeley (4 815 строк по Москве и нашим позициям) |
| `wb_sample.csv` | 2.4M | GitHub: luminati-io/Wildberries-dataset-sample — 1 001 листинг Wildberries |
| `wb_gift_reviews.csv` | 5.6M | Kaggle: реальные отзывы покупателей Wildberries, отфильтрованы по подарочной тематике (20 000 строк) |

## Open-source проекты, адаптированные в проекте

- [samirsaci/last-mile](https://github.com/samirsaci/last-mile) — VRP на Google OR-Tools с ограничениями вместимости. Адаптировано в `src/geo/routing.py` (класс `VRPSolver`): депо — хаб упаковки, точки доставки — ПВЗ в радиусе.
- [chinmai-gudivada/Instagram-Data-Analytics](https://github.com/chinmai-gudivada/Instagram-Data-Analytics) — CSV с 119 реальными Instagram-постами скопирован в проект. Аналитика источников импрешнов и Likes/Impressions реализована в `src/marketing/instagram_real.py`.
- [timurkanaz/Russia_geojson_OSM](https://github.com/timurkanaz/Russia_geojson_OSM) — GeoJSON 127 районов Москвы. Загрузка и расчёт центроидов реализованы в `src/geo/geojson_loader.py` (класс `MoscowGeoJSONLoader`).
- [luminati-io/Wildberries-dataset-sample](https://github.com/luminati-io/Wildberries-dataset-sample) — 1 001 листинг Wildberries: цены, рейтинги, отзывы. Обработка в `src/marketing/wb_analyzer.py`.
```

## Использование LLM

ChatGPT использовался для интернет-поиска подходящих open-source репозиториев, открытых датасетов. Все расчёты проверены на реальных данных, цифры в дашборде получены прогоном кода.
