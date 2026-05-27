from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.labels import MARKETPLACE_RU, translate

MOSCOW_CENTER = {"lat": 55.7522, "lon": 37.6156}


def _map_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        font=dict(family="Segoe UI, Arial, sans-serif", size=13),
        margin={"r": 0, "t": 70, "l": 0, "b": 0},
        height=620,
    )
    return fig


def _chart_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        font=dict(family="Segoe UI, Arial, sans-serif", size=13),
        margin={"r": 20, "t": 70, "l": 20, "b": 50},
        plot_bgcolor="#fafbfc", paper_bgcolor="white",
    )
    return fig


class GeoVisualizer:
    @staticmethod
    def pvz_density_map(pvz: pd.DataFrame) -> go.Figure:
        fig = px.density_mapbox(
            pvz, lat="lat", lon="lon", z="daily_orders",
            radius=22, center=MOSCOW_CENTER, zoom=10,
            mapbox_style="open-street-map",
            labels={"daily_orders": "Дневной поток заказов"},
        )
        return _map_layout(fig, "Плотность ПВЗ маркетплейсов в Москве (тепловая карта)")

    @staticmethod
    def pvz_by_marketplace(pvz: pd.DataFrame) -> go.Figure:
        d = pvz.copy()
        d["Маркетплейс"] = translate(d["marketplace"], MARKETPLACE_RU)
        fig = px.scatter_mapbox(
            d, lat="lat", lon="lon", color="Маркетплейс",
            hover_name="pvz_id",
            hover_data={"district": True, "daily_orders": True,
                        "lat": False, "lon": False, "Маркетплейс": False},
            center=MOSCOW_CENTER, zoom=10,
            mapbox_style="open-street-map",
        )
        fig.update_traces(marker=dict(size=10))
        return _map_layout(fig, "ПВЗ Ozon, Wildberries и Lamoda по районам")

    @staticmethod
    def okrug_bar(okrug_summary: pd.DataFrame) -> go.Figure:
        fig = px.bar(
            okrug_summary.sort_values("daily_orders", ascending=True),
            x="daily_orders", y="okrug", orientation="h",
            color="pvz_count", color_continuous_scale="Viridis",
            labels={"daily_orders": "Заказов в день",
                    "okrug": "Округ Москвы",
                    "pvz_count": "Кол-во ПВЗ"},
        )
        return _chart_layout(fig, "Поток заказов с маркетплейсов по округам Москвы")

    @staticmethod
    def hub_coverage_map(pvz: pd.DataFrame, hubs: pd.DataFrame,
                         radius_km: float = 8.0) -> go.Figure:
        d = pvz.copy()
        d["Маркетплейс"] = translate(d["marketplace"], MARKETPLACE_RU)
        fig = px.scatter_mapbox(
            d, lat="lat", lon="lon", color="Маркетплейс", opacity=0.55,
            zoom=10, center=MOSCOW_CENTER, mapbox_style="open-street-map",
            hover_data={"district": True, "daily_orders": True,
                        "lat": False, "lon": False, "Маркетплейс": False},
        )
        fig.update_traces(marker=dict(size=8), selector=dict(type="scattermapbox"))
        fig.add_trace(go.Scattermapbox(
            lat=hubs["lat"], lon=hubs["lon"],
            mode="markers+text",
            marker=dict(size=22, color="black", symbol="star"),
            text=hubs["hub_district"], textposition="top center",
            textfont=dict(size=14, color="black"),
            name=f"Хабы упаковки (радиус {radius_km} км)",
            hovertemplate="<b>Хаб: %{text}</b><extra></extra>",
        ))
        return _map_layout(fig, f"Рекомендуемые хабы упаковки WrapItUp (радиус покрытия {radius_km} км)")

    @staticmethod
    def distance_histogram(distance_df: pd.DataFrame) -> go.Figure:
        d = distance_df.copy()
        d["Маркетплейс"] = translate(d["marketplace"], MARKETPLACE_RU)
        fig = px.histogram(
            d, x="distance_km", nbins=30, color="Маркетплейс",
            labels={"distance_km": "Расстояние от ПВЗ до ближайшего хаба, км"},
        )
        return _chart_layout(fig, "Плечо доставки от ПВЗ до ближайшего хаба упаковки")
