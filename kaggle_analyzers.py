from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.labels import AUDIENCE_RU, CAMPAIGN_TYPE_RU, CHANNEL_RU, SEGMENT_RU, translate


def _parse_money(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.replace(r"[\$,\s]", "", regex=True)
    return pd.to_numeric(s, errors="coerce")


def _parse_duration_days(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.extract(r"(\d+)")[0]
    return pd.to_numeric(s, errors="coerce")


@dataclass
class KaggleSMMAnalyzer:
    csv_path: Path
    usd_to_rub: float = 95.0

    def load(self, sample_n: Optional[int] = None) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        if sample_n is not None and len(df) > sample_n:
            df = df.sample(n=sample_n, random_state=42).reset_index(drop=True)
        df["acquisition_cost_usd"] = _parse_money(df["Acquisition_Cost"])
        df["acquisition_cost_rub"] = df["acquisition_cost_usd"] * self.usd_to_rub
        df["duration_days"] = _parse_duration_days(df["Duration"])
        df["cpc_usd"] = df["acquisition_cost_usd"] / df["Clicks"].replace(0, np.nan)
        df["cpm_usd"] = df["acquisition_cost_usd"] / df["Impressions"].replace(0, np.nan) * 1000
        df["ctr_pct"] = df["Clicks"] / df["Impressions"].replace(0, np.nan) * 100
        return df

    def by_channel(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby("Channel_Used").agg(
                campaigns=("Campaign_ID", "count"),
                avg_roi=("ROI", "mean"),
                avg_conversion=("Conversion_Rate", "mean"),
                median_cpc_usd=("cpc_usd", "median"),
                median_cpm_usd=("cpm_usd", "median"),
                avg_ctr_pct=("ctr_pct", "mean"),
                avg_engagement=("Engagement_Score", "mean"),
            ).round(3).reset_index().sort_values("avg_roi", ascending=False)
        )

    def by_audience(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby("Target_Audience").agg(
                campaigns=("Campaign_ID", "count"),
                avg_roi=("ROI", "mean"),
                avg_conversion=("Conversion_Rate", "mean"),
                avg_engagement=("Engagement_Score", "mean"),
            ).round(3).reset_index().sort_values("avg_roi", ascending=False)
        )

    def by_segment(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby("Customer_Segment").agg(
                campaigns=("Campaign_ID", "count"),
                avg_roi=("ROI", "mean"),
                avg_engagement=("Engagement_Score", "mean"),
            ).round(3).reset_index().sort_values("avg_roi", ascending=False)
        )


@dataclass
class KaggleCampaignsAnalyzer:
    csv_path: Path

    def load(self, sample_n: Optional[int] = None) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        if sample_n is not None and len(df) > sample_n:
            df = df.sample(n=sample_n, random_state=42).reset_index(drop=True)
        df["acquisition_cost_usd"] = _parse_money(df["Acquisition_Cost"])
        df["duration_days"] = _parse_duration_days(df["Duration"])
        df["cpc_usd"] = df["acquisition_cost_usd"] / df["Clicks"].replace(0, np.nan)
        df["roi_pct"] = df["ROI"] * 100
        return df

    def by_campaign_type(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby("Campaign_Type").agg(
                campaigns=("Campaign_ID", "count"),
                avg_roi=("ROI", "mean"),
                avg_conversion=("Conversion_Rate", "mean"),
                avg_engagement=("Engagement_Score", "mean"),
                median_cost_usd=("acquisition_cost_usd", "median"),
            ).round(3).reset_index().sort_values("avg_roi", ascending=False)
        )

    def by_channel(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby("Channel_Used").agg(
                campaigns=("Campaign_ID", "count"),
                avg_roi=("ROI", "mean"),
                avg_conversion=("Conversion_Rate", "mean"),
                median_cost_usd=("acquisition_cost_usd", "median"),
            ).round(3).reset_index().sort_values("avg_roi", ascending=False)
        )


def _ru_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        font=dict(family="Segoe UI, Arial, sans-serif", size=13),
        margin={"r": 20, "t": 70, "l": 20, "b": 50},
        plot_bgcolor="#fafbfc",
        paper_bgcolor="white",
    )
    return fig


class KaggleVisualizer:
    @staticmethod
    def roi_by_channel(by_channel: pd.DataFrame, title: str) -> go.Figure:
        d = by_channel.copy()
        d["Канал"] = translate(d["Channel_Used"], CHANNEL_RU)
        fig = px.bar(
            d.sort_values("avg_roi"),
            x="avg_roi", y="Канал", orientation="h",
            color="campaigns", color_continuous_scale="Viridis",
            labels={"avg_roi": "Средний ROI (доход на 1 рубль)", "campaigns": "Кампаний в выборке"},
        )
        return _ru_layout(fig, title)

    @staticmethod
    def conversion_by_audience(by_aud: pd.DataFrame) -> go.Figure:
        d = by_aud.copy()
        d["Аудитория"] = translate(d["Target_Audience"], AUDIENCE_RU)
        fig = px.bar(
            d.sort_values("avg_conversion"),
            x="avg_conversion", y="Аудитория", orientation="h",
            color="avg_roi", color_continuous_scale="RdYlGn",
            labels={"avg_conversion": "Средняя конверсия в покупку",
                    "avg_roi": "ROI"},
        )
        return _ru_layout(fig, "Конверсия в покупку по сегментам аудитории")

    @staticmethod
    def roi_distribution(df: pd.DataFrame) -> go.Figure:
        d = df.copy()
        d["Канал"] = translate(d["Channel_Used"], CHANNEL_RU)
        fig = px.histogram(
            d, x="ROI", color="Канал", nbins=40,
            labels={"ROI": "Значение ROI"},
        )
        return _ru_layout(fig, "Распределение ROI по каналам (выборка 5000 кампаний)")

    @staticmethod
    def roi_by_campaign_type(by_type: pd.DataFrame) -> go.Figure:
        d = by_type.copy()
        d["Тип кампании"] = translate(d["Campaign_Type"], CAMPAIGN_TYPE_RU)
        fig = px.bar(
            d.sort_values("avg_roi"),
            x="avg_roi", y="Тип кампании", orientation="h",
            color="avg_conversion", color_continuous_scale="Viridis",
            labels={"avg_roi": "Средний ROI", "avg_conversion": "Конверсия"},
        )
        return _ru_layout(fig, "ROI по типам маркетинговых кампаний")
