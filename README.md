# WrapItUp

Проект курса «Наука о Данных», весна 2026. Сервис подарочной упаковки товаров с маркетплейсов (Ozon, Wildberries, Lamoda) с доставкой клиенту. B2C-формат: клиент оформляет заказ на маркетплейсе с самовывозом в ПВЗ, WrapItUp забирает товар, упаковывает и привозит получателю курьером.

## Структура репозитория

В `main` — общий план и сводный README. Каждый участник работает в своей ветке.

| Ветка | Раздел |
|---|---|
| `main` | общий план команды |
| `geo-marketing` | География + Маркетинг |

## Разделы (из методички)

1. Целевая аудитория
2. Конкуренты
3. Бизнес-окружение
4. Маркетинговая кампания
5. География компании
6. Сотрудники

## Технологии курса

- ООП-стиль кода: 15+ классов в `src/geo/` и `src/marketing/`.
- Интерактивный дашборд на Dash: `dashboard/app.py`, 9 вкладок, 2 callback.
- Стат-тест Уэлча (`scipy.stats.ttest_ind`).
- VRP-оптимизация маршрутов: Google OR-Tools.
- OLS-регрессия (Plotly trendline на Instagram-датасете).
- Работа с GeoJSON (Polygon/MultiPolygon → центроиды).

## Запуск локально

```bash
pip install -r requirements.txt

python -m src.build_processed_data
python dashboard/app.py
```

После запуска дашборд доступен по адресу `http://127.0.0.1:8050`.

## Состав данных в `data/raw/`

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

## Индексация зарплат

Данные Mendeley собраны в 2023 году. К полям `salary_from` и `salary_to` применён накопительный коэффициент номинального роста по данным Росстата:

```
2023 → 2024:  +18.3%  (Росстат, номинальная средняя ЗП 74 854 → 87 952 ₽)
2024 → 2025:  +14.5%  (Росстат, май 2025)
2025 → 2026:  +11%    (макроэкономический прогноз Банка России)
итого:  1.183 × 1.145 × 1.11 ≈ 1.50
```

## Использование LLM

ChatGPT использовался для интернет-поиска подходящих open-source репозиториев, открытых датасетов и проверки коэффициента индексации зарплат по данным Росстата. Все расчёты проверены на реальных данных, цифры в дашборде получены прогоном кода.

## Дерево проекта

```
WrapItUp-Project/
├── README.md
├── requirements.txt, .gitignore
├── data/
│   ├── raw/        ← исходные датасеты
│   └── processed/  ← генерируется командой build_processed_data
├── src/
│   ├── geo/
│   │   ├── data_loader.py
│   │   ├── analyzer.py
│   │   ├── visualizer.py
│   │   ├── routing.py
│   │   └── geojson_loader.py
│   ├── marketing/
│   │   ├── data_loader.py, analyzer.py, visualizer.py
│   │   ├── instagram_real.py
│   │   ├── hh_fetcher.py, hh_analyzer.py
│   │   ├── kaggle_analyzers.py
│   │   └── wb_analyzer.py
│   ├── labels.py
│   └── build_processed_data.py
├── notebooks/01_geo_and_marketing_analysis.ipynb
├── dashboard/app.py
└── reports/branch_README.md, business_recommendations.md
```
