from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.labels import NICHE_RU, translate


def _ru_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        font=dict(family="Segoe UI, Arial, sans-serif", size=13),
        margin={"r": 20, "t": 70, "l": 20, "b": 50},
        plot_bgcolor="#fafbfc", paper_bgcolor="white",
    )
    return fig


class MarketingVisualizer:
    @staticmethod
    def roas_bar(channel_eff: pd.DataFrame) -> go.Figure:
        fig = px.bar(
            channel_eff.sort_values("roas", ascending=True),
            x="roas", y="channel", orientation="h",
            color="avg_engagement_rate_pct", color_continuous_scale="Viridis",
            labels={"roas": "ROAS (выручка ÷ затраты на рекламу)",
                    "channel": "Канал",
                    "avg_engagement_rate_pct": "Engagement Rate, %"},
        )
        return _ru_layout(fig, "ROAS по 12 рекламным каналам (бенчмарк проекта)")

    @staticmethod
    def cpm_vs_engagement(channel_eff: pd.DataFrame) -> go.Figure:
        fig = px.scatter(
            channel_eff,
            x="avg_cpm_rub", y="avg_engagement_rate_pct",
            size="reach_per_post", color="channel", hover_name="channel",
            labels={"avg_cpm_rub": "CPM (стоимость 1000 показов), руб",
                    "avg_engagement_rate_pct": "Engagement Rate, %",
                    "reach_per_post": "Охват за пост", "channel": "Канал"},
        )
        return _ru_layout(fig, "Связь стоимости показов (CPM) и вовлечённости")

    @staticmethod
    def budget_allocation_pie(plan: pd.DataFrame) -> go.Figure:
        fig = px.pie(plan, names="channel", values="budget_rub", hole=0.45)
        return _ru_layout(fig, "Распределение бюджета по каналам")

    @staticmethod
    def competitor_engagement(competitors: pd.DataFrame) -> go.Figure:
        d = competitors.copy()
        d["Ниша"] = translate(d["niche"], NICHE_RU)
        fig = px.scatter(
            d, x="followers", y="engagement_rate_pct",
            size="avg_views", color="Ниша", hover_name="account",
            labels={"followers": "Подписчиков",
                    "engagement_rate_pct": "Engagement Rate, %",
                    "avg_views": "Среднее число просмотров"},
        )
        fig.update_xaxes(type="log")
        return _ru_layout(fig, "Конкуренты по нише: подписчики и ER")

    @staticmethod
    def kpi_indicators(kpis: dict) -> go.Figure:
        fig = go.Figure()
        fig.add_trace(go.Indicator(
            mode="number", value=kpis["total_reach"],
            title={"text": "Прогноз охвата"},
            domain={"row": 0, "column": 0}))
        fig.add_trace(go.Indicator(
            mode="number", value=kpis["total_orders"],
            title={"text": "Прогноз заказов"},
            domain={"row": 0, "column": 1}))
        fig.add_trace(go.Indicator(
            mode="number", value=kpis["total_revenue_rub"],
            number={"prefix": "₽ ", "valueformat": ",.0f"},
            title={"text": "Прогноз выручки"},
            domain={"row": 0, "column": 2}))
        fig.add_trace(go.Indicator(
            mode="number", value=kpis["blended_roas"],
            title={"text": "Средний ROAS"},
            domain={"row": 0, "column": 3}))
        fig.update_layout(
            grid={"rows": 1, "columns": 4, "pattern": "independent"},
            margin={"r": 20, "t": 40, "l": 20, "b": 20}, height=210,
            font=dict(family="Segoe UI, Arial, sans-serif", size=14),
        )
        return fig
