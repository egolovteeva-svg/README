from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
from dash import Dash, dcc, html, Input, Output

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.geo import GeoAnalyzer, GeoVisualizer
from src.marketing import (
    CampaignAnalyzer, CompetitorAnalyzer,
    HHAnalyzer, HHVisualizer,
    InstagramRealDataAnalyzer, InstagramRealVisualizer,
    KaggleVisualizer, MarketingVisualizer,
    WBVisualizer,
)
from src.labels import SEGMENT_RU, AUDIENCE_RU

PROC = ROOT / "data" / "processed"
RAW = ROOT / "data" / "raw"


def _read(name: str) -> pd.DataFrame:
    p = PROC / name
    if not p.exists():
        raise FileNotFoundError(
            f"Не найден {p}. Сначала выполни: python -m src.build_processed_data")
    return pd.read_csv(p)


def _opt(name: str):
    p = PROC / name
    return pd.read_csv(p) if p.exists() else None


districts = _read("districts_enriched.csv")
pvz = _read("pvz.csv")
okrug = _read("okrug_summary.csv")
hubs = _read("hub_locations.csv")
distance_df = _read("delivery_distance.csv")
channels = _read("channel_efficiency.csv")
budget_plan = _read("budget_plan.csv")
competitors = _read("competitors_bench.csv")

geo_an = GeoAnalyzer(districts=districts, pvz=pvz)
camp_an = CampaignAnalyzer(channels=channels)
comp_an = CompetitorAnalyzer(competitors=competitors)
kpis = camp_an.funnel_kpis(budget_rub=500_000)
er_test = comp_an.er_difference_test()

geo_viz = GeoVisualizer()
mkt_viz = MarketingVisualizer()
ig_viz = InstagramRealVisualizer()
hh_viz = HHVisualizer()
kg_viz = KaggleVisualizer()
wb_viz = WBVisualizer()

ig_df = _opt("instagram_real.csv")
ig_sources = _opt("instagram_sources.csv")
ig_corr = pd.read_csv(PROC / "instagram_corr.csv", index_col=0) if (PROC / "instagram_corr.csv").exists() else None
ig_top = None
if ig_df is not None:
    ig_top = InstagramRealDataAnalyzer(
        RAW / "instagram_real_dataset.csv"
    ).top_posts_by_engagement(ig_df, n=10)

hh_df = _opt("hh_clean.csv")
hh_by_query = _opt("hh_by_query.csv")
team_cost = {}
if hh_df is not None:
    hh_an = HHAnalyzer(RAW / "hh_vacancies_moscow.csv")
    team_cost = hh_an.total_team_cost(hh_df, positions={
        "marketing": 1, "smm": 1, "targeting": 1,
        "gift_packer": 6, "courier": 10, "marketplace_manager": 1,
    })

smm_by_channel = _opt("kaggle_smm_by_channel.csv")
smm_by_audience = _opt("kaggle_smm_by_audience.csv")
smm_by_segment = _opt("kaggle_smm_by_segment.csv")
smm_sample = _opt("kaggle_smm_sample.csv")
mc_by_type = _opt("kaggle_mc_by_type.csv")
mc_by_channel = _opt("kaggle_mc_by_channel.csv")

wb_by_cat = _opt("wb_by_category.csv")
wb_clean = _opt("wb_clean.csv")
wb_reviews_summary = _opt("wb_reviews_summary.csv")
wb_reviews_by_keyword = _opt("wb_reviews_by_keyword.csv")


COLORS = {
    "primary": "#2c5282", "accent": "#4a90e2",
    "bg": "#f7f9fc", "card_bg": "white",
    "text": "#1a202c", "muted": "#4a5568",
    "border": "#e2e8f0",
    "good": "#2f855a", "warn": "#c05621", "bad": "#c53030",
}

CARD = {
    "background": COLORS["card_bg"], "padding": "18px 22px",
    "borderRadius": "10px", "boxShadow": "0 1px 3px rgba(0,0,0,0.08)",
    "marginBottom": "20px", "border": f"1px solid {COLORS['border']}",
}

EXPLAIN_STYLE = {
    "background": "#eef5ff", "padding": "12px 16px",
    "borderRadius": "8px", "borderLeft": f"4px solid {COLORS['accent']}",
    "marginBottom": "14px", "color": COLORS["text"],
    "fontSize": "14px", "lineHeight": "1.55",
}

MAP_CONFIG = {
    "scrollZoom": True, "displayModeBar": True, "displaylogo": False,
    "modeBarButtonsToAdd": ["zoomIn2d", "zoomOut2d"],
    "toImageButtonOptions": {"format": "png", "filename": "WrapItUp_map"},
}
CHART_CONFIG = {"displayModeBar": True, "displaylogo": False}


def explain(text):
    return html.Div(text, style=EXPLAIN_STYLE)


def section_title(text):
    return html.H3(text, style={"color": COLORS["primary"], "marginTop": "10px",
                                "marginBottom": "14px", "fontSize": "20px"})


def subsection(text):
    return html.H4(text, style={"color": COLORS["primary"], "marginTop": "14px",
                                "marginBottom": "10px", "fontSize": "16px"})


def colored_badge(text, color):
    return html.Span(text, style={
        "background": color, "color": "white", "padding": "4px 10px",
        "borderRadius": "12px", "fontSize": "12px", "fontWeight": "600",
        "display": "inline-block",
    })


def rich_table(rows: list[dict], cols: list[str]):
    """Таблица с поддержкой ячеек-Dash-компонентов."""
    return html.Table(
        [html.Thead(html.Tr([html.Th(c, style={"padding": "10px 12px",
                                               "background": COLORS["primary"],
                                               "color": "white",
                                               "textAlign": "left",
                                               "fontSize": "13px"}) for c in cols]))] +
        [html.Tbody([
            html.Tr([
                html.Td(row.get(c, ""),
                        style={"padding": "10px 12px",
                               "borderBottom": f"1px solid {COLORS['border']}",
                               "fontSize": "13px", "verticalAlign": "top"})
                for c in cols
            ]) for row in rows
        ])],
        style={"width": "100%", "borderCollapse": "collapse",
               "marginTop": "10px", "marginBottom": "10px"},
    )


def build_segments_data():
    rows = []
    if smm_by_segment is not None:
        for _, r in smm_by_segment.iterrows():
            seg_en = r["Customer_Segment"]
            seg_ru = SEGMENT_RU.get(seg_en, seg_en)
            roi = float(r["avg_roi"])
            if roi >= 3.20:
                rec = "Высокий приоритет. Запускаем кампанию в первую очередь."
                badge = colored_badge(f"ROI {roi:.2f} ★★★", COLORS["good"])
            elif roi >= 3.15:
                rec = "Средний приоритет. Подключаем второй очередью, тестируем креативы."
                badge = colored_badge(f"ROI {roi:.2f} ★★", COLORS["warn"])
            else:
                rec = "Низкий приоритет. Берём только при свободном бюджете."
                badge = colored_badge(f"ROI {roi:.2f} ★", COLORS["bad"])
            rows.append({
                "Сегмент аудитории": html.B(seg_ru),
                "Эффективность": badge,
                "Кампаний в выборке": f"{int(r['campaigns']):,}".replace(",", " "),
                "Вовлечённость": f"{r['avg_engagement']:.2f}",
                "Рекомендация": rec,
                "Источник": html.Span("Kaggle SMM 300K", style={"color": COLORS["muted"], "fontSize": "12px"}),
            })
    if smm_by_audience is not None:
        top_aud = smm_by_audience.head(6)
        for _, r in top_aud.iterrows():
            aud_en = r["Target_Audience"]
            aud_ru = AUDIENCE_RU.get(aud_en, aud_en)
            roi = float(r["avg_roi"])
            conv = float(r["avg_conversion"])
            if roi >= 3.25 and conv >= 0.08:
                rec = "Топ-аудитория. На неё льём 30-40% бюджета."
                badge = colored_badge(f"ROI {roi:.2f}", COLORS["good"])
            elif roi >= 3.20:
                rec = "Хорошая аудитория. Добавляем в круг тестируемых."
                badge = colored_badge(f"ROI {roi:.2f}", COLORS["warn"])
            else:
                rec = "Слабая по ROI — пропускаем, либо тестируем минимальным бюджетом."
                badge = colored_badge(f"ROI {roi:.2f}", COLORS["bad"])
            rows.append({
                "Сегмент аудитории": html.B(aud_ru),
                "Эффективность": badge,
                "Кампаний в выборке": f"{int(r['campaigns']):,}".replace(",", " "),
                "Вовлечённость": f"{r['avg_engagement']:.2f}",
                "Рекомендация": rec,
                "Источник": html.Span("Kaggle SMM (по аудиториям)", style={"color": COLORS["muted"], "fontSize": "12px"}),
            })
    if wb_reviews_by_keyword is not None:
        for _, r in wb_reviews_by_keyword.head(6).iterrows():
            share = float(r["доля_про_подарок_pct"])
            mark = float(r["средняя_оценка"])
            if share >= 5:
                rec = "Сильная подарочная связка — оформляем спец-предложение."
                badge = colored_badge(f"{share:.1f}% подарков", COLORS["good"])
            elif share >= 2:
                rec = "Подарочная активность есть. Добавляем в маркетинг сезонно."
                badge = colored_badge(f"{share:.1f}%", COLORS["warn"])
            else:
                rec = "Подарочная тема почти не упоминается — не приоритет."
                badge = colored_badge(f"{share:.1f}%", COLORS["bad"])
            rows.append({
                "Сегмент аудитории": html.B(f"WB: {r['keyword']}"),
                "Эффективность": badge,
                "Кампаний в выборке": f"{int(r['отзывов']):,}".replace(",", " ") + " отзывов",
                "Вовлечённость": f"оценка {mark:.2f}",
                "Рекомендация": rec,
                "Источник": html.Span("Wildberries 20K отзывов", style={"color": COLORS["muted"], "fontSize": "12px"}),
            })
    return rows


segments_rows = build_segments_data()


geo_tab = dcc.Tab(label="🗺 География", children=[
    html.Div([
        section_title("Где открывать хабы упаковки в Москве"),
        explain(
            "На карте — ПВЗ маркетплейсов (Ozon, Wildberries, Lamoda) "
            "и предлагаемые локации хабов упаковки (звёзды). Координаты районов "
            "взяты из реального GeoJSON Москвы (OpenStreetMap). "
            "Карту можно крутить колесом мыши и масштабировать кнопками «+ / −» "
            "в правом верхнем углу карты. Двигай ползунок ниже — увидишь, "
            "как меняется расположение хабов при разных радиусах."
        ),
        html.Label("Радиус покрытия одного хаба (км):",
                   style={"fontWeight": "600", "marginBottom": "8px"}),
        dcc.Slider(id="radius-slider", min=3, max=15, step=1, value=8,
                   marks={i: f"{i} км" for i in range(3, 16, 2)}),
        html.Div(style={"height": "10px"}),
        dcc.Graph(id="hub-map", config=MAP_CONFIG),
    ], style=CARD),

    html.Div([
        subsection("Какие округа дают больше всего заказов"),
        explain("Чем длиннее столбец, тем выше суточная нагрузка на инфраструктуру "
                "маркетплейсов в округе. Цвет — кол-во ПВЗ."),
        dcc.Graph(figure=geo_viz.okrug_bar(okrug), config=CHART_CONFIG),
    ], style=CARD),

    html.Div([
        subsection("Тепловая карта плотности заказов"),
        explain("Чем краснее зона, тем выше суточный поток заказов с маркетплейсов."),
        dcc.Graph(figure=geo_viz.pvz_density_map(pvz), config=MAP_CONFIG),
    ], style=CARD),

    html.Div([
        subsection("Плечо доставки от ПВЗ до ближайшего хаба"),
        explain("Гистограмма: сколько километров курьеру в среднем ездить. "
                "Чем «левее» гора, тем короче среднее плечо."),
        dcc.Graph(figure=geo_viz.distance_histogram(distance_df), config=CHART_CONFIG),
    ], style=CARD),
])


mkt_tab = dcc.Tab(label="📈 Маркетинг", children=[
    html.Div([
        section_title("Прогноз ключевых показателей кампании"),
        explain("Большие цифры — прогноз при бюджете 500 000 ₽. "
                "ROAS = выручка ÷ затраты. Ползунок ниже меняет бюджет и пересчитывает раскладку."),
        dcc.Graph(id="kpi-indicators", figure=mkt_viz.kpi_indicators(kpis),
                  config=CHART_CONFIG),
        html.Label("Бюджет кампании (₽):",
                   style={"fontWeight": "600", "marginTop": "10px", "marginBottom": "8px"}),
        dcc.Slider(id="budget-slider", min=100_000, max=2_000_000, step=50_000, value=500_000,
                   marks={100_000: "100K", 500_000: "500K",
                          1_000_000: "1M", 2_000_000: "2M"}),
        html.Div(style={"height": "10px"}),
        dcc.Graph(id="budget-pie", config=CHART_CONFIG),
    ], style=CARD),

    html.Div([
        subsection("ROAS и связь CPM / Engagement по каналам"),
        explain("Слева: ROAS (выручка на 1 ₽ рекламы) по 12 каналам. "
                "Справа: чем точка выше, тем выше вовлечённость, чем правее — дороже показы."),
        html.Div([
            dcc.Graph(figure=mkt_viz.roas_bar(channels), config=CHART_CONFIG,
                      style={"display": "inline-block", "width": "49%"}),
            dcc.Graph(figure=mkt_viz.cpm_vs_engagement(channels), config=CHART_CONFIG,
                      style={"display": "inline-block", "width": "49%"}),
        ]),
    ], style=CARD),

    html.Div([
        subsection("Конкуренты в Instagram по нише подарков"),
        dcc.Graph(figure=mkt_viz.competitor_engagement(competitors), config=CHART_CONFIG),
    ], style=CARD),

    html.Div([
        subsection("Статистическая гипотеза"),
        explain("Проверка t-тестом Уэлча: значимо ли ER у «Подарочной упаковки» выше, "
                "чем у «Доставки подарков»."),
        html.Pre(str(er_test), style={"background": "#f6f8fa", "padding": "12px",
                                       "borderRadius": "6px", "fontSize": "13px"}),
    ], style=CARD),
])


ig_tab = dcc.Tab(label="📷 Instagram", children=(
    [html.Div([
        section_title("Реальный Instagram-датасет — 119 постов"),
        explain("Открытый датасет с метриками постов (Likes, Comments, Shares, Saves, "
                "Impressions, источники). Проверяем SMM-гипотезы на живых цифрах."),
        html.Div([
            dcc.Graph(figure=ig_viz.impressions_pie(ig_sources), config=CHART_CONFIG,
                      style={"display": "inline-block", "width": "49%"}),
            dcc.Graph(figure=ig_viz.er_distribution(ig_df), config=CHART_CONFIG,
                      style={"display": "inline-block", "width": "49%"}),
        ]),
        explain("Вывод: 44% показов из домашней ленты, 34% — через хештеги. "
                "Работа с тегами критически важна для нашей ниши."),
    ], style=CARD),

    html.Div([
        subsection("Лайки и охват"),
        dcc.Graph(figure=ig_viz.likes_vs_impressions(ig_df), config=CHART_CONFIG),
    ], style=CARD),

    html.Div([
        subsection("Тепловая карта связей между метриками"),
        dcc.Graph(figure=ig_viz.correlation_heatmap(ig_corr), config=CHART_CONFIG),
    ], style=CARD),
    ] if ig_df is not None else
    [html.Div([html.H3("Instagram-датасет не загружен")], style=CARD)]
))


kaggle_smm_tab = dcc.Tab(label="📊 SMM (300K)", children=(
    [html.Div([
        section_title("300 000 рекламных кампаний — Kaggle SMM"),
        explain("Большой реальный датасет: Facebook, Instagram, Twitter, Pinterest. "
                "Стоимость, охват, клики, ROI."),
        dcc.Graph(figure=kg_viz.roi_by_channel(
            smm_by_channel, title="Средний ROI по каналам (выборка 50K)"),
            config=CHART_CONFIG),
        explain("Главный вывод: Facebook, Instagram, Twitter — ROI ~4. "
                "Pinterest — ROI 0.71. Pinterest исключаем из плана."),
    ], style=CARD),

    html.Div([
        subsection("Какая аудитория конвертируется лучше"),
        dcc.Graph(figure=kg_viz.conversion_by_audience(smm_by_audience), config=CHART_CONFIG),
    ], style=CARD),

    html.Div([
        subsection("Распределение ROI"),
        dcc.Graph(figure=kg_viz.roi_distribution(smm_sample), config=CHART_CONFIG),
    ], style=CARD),
    ] if smm_by_channel is not None else
    [html.Div([html.H3("Датасет не загружен")], style=CARD)]
))


kaggle_mc_tab = dcc.Tab(label="📊 Кампании (200K)", children=(
    [html.Div([
        section_title("200 000 кампаний — Kaggle Marketing"),
        explain("Email, поисковая реклама, медийка, инфлюенсеры, соцсети."),
        dcc.Graph(figure=kg_viz.roi_by_campaign_type(mc_by_type), config=CHART_CONFIG),
    ], style=CARD),

    html.Div([
        subsection("ROI по каналам"),
        dcc.Graph(figure=kg_viz.roi_by_channel(mc_by_channel, title="ROI по каналам"),
                  config=CHART_CONFIG),
    ], style=CARD),
    ] if mc_by_type is not None else
    [html.Div([html.H3("Датасет не загружен")], style=CARD)]
))


wb_tab = dcc.Tab(label="🛒 Wildberries", children=(
    [html.Div([
        section_title("Wildberries — 1001 реальный листинг товаров"),
        explain([
            "Открытый датасет: ", html.B("1001 товар Wildberries"),
            " с реальными ценами, рейтингами, скидками и количеством отзывов. "
            "Источник: GitHub luminati-io/Wildberries-dataset-sample."]),
        dcc.Graph(figure=wb_viz.category_prices_bar(wb_by_cat) if wb_by_cat is not None
                  else go_empty(), config=CHART_CONFIG),
    ], style=CARD) if wb_by_cat is not None else html.Div(style=CARD),

    html.Div([
        section_title("20 000 реальных отзывов покупателей про подарки"),
        explain([
            "Стрим-фильтрация 1.5 GB-датасета отзывов WB: отобрали ", html.B("20 000 отзывов"),
            ", где упоминаются «подарок», «упаковка», «сюрприз», «праздник». "
            "Видим, в каких категориях товар чаще всего покупают как подарок."]),
        rich_table(
            [{"Метрика": "Всего отзывов в выборке",
              "Значение": html.B(f"{int(wb_reviews_summary['всего_отзывов'][0]):,}".replace(",", " "))},
             {"Метрика": "Упомянули подарок/упаковку",
              "Значение": html.B(f"{int(wb_reviews_summary['упомянули_подарок'][0]):,}".replace(",", " "))},
             {"Метрика": "Позитивных отзывов",
              "Значение": colored_badge(f"{int(wb_reviews_summary['позитивных'][0]):,}".replace(",", " "), COLORS["good"])},
             {"Метрика": "Негативных отзывов",
              "Значение": colored_badge(f"{int(wb_reviews_summary['негативных'][0]):,}".replace(",", " "), COLORS["bad"])},
             {"Метрика": "Средняя оценка (из 5)",
              "Значение": html.B(f"{float(wb_reviews_summary['средняя_оценка'][0]):.2f}")},
             {"Метрика": "Доля 5 звёзд",
              "Значение": html.B(f"{float(wb_reviews_summary['доля_5_звёзд_pct'][0]):.1f}%")},
            ],
            ["Метрика", "Значение"],
        ) if wb_reviews_summary is not None else html.P("WB отзывы не загружены"),
    ], style=CARD),

    html.Div([
        subsection("Топ категорий по числу отзывов с подарочной тематикой"),
        explain("Чем оранжевее столбец, тем чаще покупатели в этой категории "
                "пишут про подарки. Это ниши, где WrapItUp найдёт спрос."),
        dcc.Graph(figure=wb_viz.keyword_bar(wb_reviews_by_keyword), config=CHART_CONFIG),
    ], style=CARD) if wb_reviews_by_keyword is not None else html.Div(style=CARD),
    ]
))


segments_tab = dcc.Tab(label="🎯 Сегменты", children=[
    html.Div([
        section_title("Сегменты аудитории — ROI и рекомендации"),
        explain([
            "В таблице ниже собраны разные срезы клиентов с реальными метриками. ",
            html.B("Источники: "),
            "Kaggle SMM (300K кампаний) по сегментам интересов и возрастам, ",
            "Wildberries (20K реальных отзывов) — категории товаров, где чаще всего упоминают подарки. ",
            "Для каждого сегмента — конкретная ",
            html.B("рекомендация"), ": куда вкладывать рекламу, кого исключать.",
        ]),
        html.Div([
            colored_badge("Высокий приоритет (★★★)", COLORS["good"]), " ",
            colored_badge("Средний (★★)", COLORS["warn"]), " ",
            colored_badge("Низкий (★)", COLORS["bad"]),
        ], style={"marginBottom": "16px"}),
        rich_table(
            segments_rows,
            ["Сегмент аудитории", "Эффективность", "Кампаний в выборке",
             "Вовлечённость", "Рекомендация", "Источник"],
        ) if segments_rows else html.P("Запусти build_processed_data для генерации"),
    ], style=CARD),

    html.Div([
        subsection("Стратегия по сегментам"),
        dcc.Markdown(
            """
**Топ-сегменты (★★★) → приоритетные.** Льём 60–70% бюджета. Для них пишем
персонализированные креативы, тестируем разные посылки, наращиваем долю охвата.

**Средние (★★) → второй очередью.** Тестируем минимальным бюджетом, смотрим
CPC и ER. Если окупаются — переводим в высокий приоритет.

**Низкие (★) → исключаем.** Не вкладываем рекламные деньги, не тратим время
команды. Если очень нужно — только органические каналы (бесплатные посевы,
сообщества).
            """,
            style={"lineHeight": "1.7", "fontSize": "14px"}),
    ], style=CARD),
])


def team_table(breakdown: pd.DataFrame):
    return html.Table(
        [html.Thead(html.Tr([html.Th(c, style={"padding": "8px 12px",
                                               "background": COLORS["primary"],
                                               "color": "white",
                                               "textAlign": "left",
                                               "fontSize": "13px"}) for c in breakdown.columns]))] +
        [html.Tbody([html.Tr(
            [html.Td(f"{v:,}".replace(",", " ") if isinstance(v, (int, float)) else v,
                     style={"padding": "8px 12px",
                            "borderBottom": f"1px solid {COLORS['border']}",
                            "fontSize": "13px"})
             for v in row]) for row in breakdown.values.tolist()])],
        style={"width": "100%", "borderCollapse": "collapse",
               "marginTop": "10px", "marginBottom": "10px"},
    )


hh_tab = dcc.Tab(label="👥 Команда", children=(
    [html.Div([
        section_title("Зарплаты в Москве и затраты на команду"),
        explain([
            "Все цифры — на основе ", html.B("4 815 реальных вакансий"),
            " из Москвы (Mendeley 2023, hh.ru + trudvsem). Зарплаты ",
            html.B("проиндексированы ×1.50"),
            " по данным Росстата (2023→2024→2025→2026: 18.3% × 14.5% × 11% ≈ +50%)."]),
        html.Div([
            dcc.Graph(figure=hh_viz.median_bar(hh_by_query), config=CHART_CONFIG,
                      style={"display": "inline-block", "width": "49%"}),
            dcc.Graph(figure=hh_viz.schedule_pie(hh_df), config=CHART_CONFIG,
                      style={"display": "inline-block", "width": "49%"}),
        ]),
    ], style=CARD),

    html.Div([
        subsection("Что такое box plot («ящик с усами»)"),
        explain([
            html.Ul([
                html.Li("линия посередине ящика — медианная зарплата"),
                html.Li("сам ящик — диапазон, в который попадают 50% вакансий "
                        "(от 25-го до 75-го процентиля)"),
                html.Li("«усы» сверху и снизу — крайние нормальные значения"),
                html.Li("отдельные точки — выбросы, нетипично высокие или низкие предложения"),
            ]),
            "Чем шире ящик, тем больше разброс ЗП внутри позиции."]),
        dcc.Graph(figure=hh_viz.salary_box(hh_df), config=CHART_CONFIG),
    ], style=CARD),

    html.Div([
        subsection("Состав и стоимость команды"),
        explain(["Стартовая команда WrapItUp: 1 маркетолог + 1 SMM + 1 таргетолог + "
                 "6 упаковщиков + 10 курьеров + 1 менеджер маркетплейсов = ",
                 html.B("20 человек"),
                 ". К ЗП прибавлено 30% на бенефиты."]),
        team_table(team_cost["breakdown"]),
        html.Div([
            html.Div([
                html.Div("Затраты в месяц", style={"color": COLORS["muted"], "fontSize": "13px"}),
                html.Div(f"{team_cost['monthly_total_rub']:,.0f} ₽".replace(",", " "),
                         style={"fontSize": "26px", "fontWeight": "700",
                                "color": COLORS["primary"]}),
            ], style={"display": "inline-block", "marginRight": "40px"}),
            html.Div([
                html.Div("Затраты в год", style={"color": COLORS["muted"], "fontSize": "13px"}),
                html.Div(f"{team_cost['annual_total_rub']:,.0f} ₽".replace(",", " "),
                         style={"fontSize": "26px", "fontWeight": "700",
                                "color": COLORS["primary"]}),
            ], style={"display": "inline-block"}),
        ], style={"marginTop": "16px"}),
    ], style=CARD),
    ] if hh_df is not None else
    [html.Div([html.H3("Данные не подгружены")], style=CARD)]
))


reco_tab = dcc.Tab(label="🎯 Рекомендации", children=[
    html.Div([
        section_title("Главные выводы и рекомендации"),
        dcc.Markdown(
            """
**География.** Оптимальные хабы упаковки — Останкинский, Зюзино, Соколиная Гора,
Покровское-Стрешнево. Среднее плечо доставки 6.5 км — городская «последняя миля».

**Маркетинг.** Kaggle SMM (300K кампаний): Facebook, Instagram, Twitter — ROI ~4,
Pinterest — 0.71, исключаем. Наш бенчмарк по каналам: TikTok, VK Клипы, YouTube Shorts.

**Instagram (real).** 44% показов из домашней ленты, 34% из хештегов — работа с тегами критична.

**Wildberries (real).** 20 000 отзывов: средняя оценка 4.62, 80.6% — пятёрки.
Подарочная тематика чаще всего встречается в категориях «Бельё», «Большие размеры»,
«Платья и сарафаны». Сезон 8 марта / 14 февраля / Новый год — пик.

**Команда.** 4815 вакансий + индексация Росстата ×1.50: маркетолог 135K, курьер 132K,
упаковщик 105K, SMM 97K. Команда из 20 человек: 3.10 млн ₽/мес, 37.2 млн ₽/год.

**KPI на первый квартал:**
- бюджет рекламы 1.5 млн ₽
- охват 4–5 млн
- 3.5–4.5 тысячи заказов из digital
- CAC до 350 ₽
- средний ROAS от 2.5
- SLA «упаковка + доставка ≤ 24 ч» от 92%
            """,
            style={"lineHeight": "1.7", "fontSize": "15px"}),
    ], style=CARD),
])


def go_empty():
    import plotly.graph_objects as go
    return go.Figure()


app = Dash(__name__, title="WrapItUp — Аналитика")
app.layout = html.Div([
    html.Div([
        html.H1("WrapItUp — Аналитика бизнеса",
                style={"color": COLORS["primary"], "marginBottom": "6px"}),
        html.P("Подарочная упаковка товаров с маркетплейсов (Ozon, Wildberries, Lamoda) "
               "с доставкой клиенту",
               style={"color": COLORS["muted"], "fontSize": "15px", "marginTop": "0"}),
    ], style={"padding": "24px 32px 0 32px"}),
    dcc.Tabs([geo_tab, mkt_tab, ig_tab, kaggle_smm_tab, kaggle_mc_tab,
              wb_tab, segments_tab, hh_tab, reco_tab],
             style={"padding": "0 32px"}),
    html.Div(style={"height": "30px"}),
], style={
    "fontFamily": "Segoe UI, system-ui, -apple-system, Roboto, Arial, sans-serif",
    "background": COLORS["bg"], "minHeight": "100vh", "color": COLORS["text"],
})


@app.callback(Output("hub-map", "figure"), Input("radius-slider", "value"))
def update_hub_map(radius_km: int):
    hubs_local = geo_an.greedy_hub_locations(n_hubs=4, radius_km=radius_km)
    return geo_viz.hub_coverage_map(pvz, hubs_local, radius_km=radius_km)


@app.callback(
    [Output("budget-pie", "figure"), Output("kpi-indicators", "figure")],
    Input("budget-slider", "value"),
)
def update_budget(budget: int):
    plan = camp_an.allocate_budget(total_budget_rub=budget)
    new_kpis = camp_an.funnel_kpis(budget_rub=budget)
    return mk