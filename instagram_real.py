from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


SOURCES_RU = {
    "From Home": "Из домашней ленты",
    "From Hashtags": "Через хештеги",
    "From Explore": "Через раздел «Интересное»",
    "From Other": "Другое",
}


@dataclass
class InstagramRealDataAnalyzer:
    csv_path: Path

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path, encoding="latin-1")
        df["engagement"] = df["Likes"] + df["Comments"] + df["Saves"] + df["Shares"]
        df["er_per_impression_pct"] = (df["engagement"] / df["Impressions"]) * 100
        df["follows_per_visit_pct"] = (
            df["Follows"] / df["Profile Visits"].replace(0, np.nan)) * 100
        return df

    def impressions_sources_breakdown(self, df: pd.DataFrame) -> pd.DataFrame:
        sources = ["From Home", "From Hashtags", "From Explore", "From Other"]
        totals = df[sources].sum()
        out = pd.DataFrame({"source": sources, "impressions": totals.values})
        out["share_pct"] = (out["impressions"] / out["impressions"].sum() * 100).round(1)
        return out

    def correlation_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        cols = ["Impressions", "From Home", "From Hashtags", "From Explore",
                "Likes", "Comments", "Saves", "Shares", "Profile Visits", "Follows"]
        return df[cols].corr().round(2)

    def hashtag_frequency(self, df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
        tags: list[str] = []
        for raw in df["Hashtags"].fillna(""):
            for piece in str(raw).replace("�", " ").replace("#", " #").split():
                p = piece.strip()
                if p.startswith("#") and len(p) > 2:
                    tags.append(p.lower())
        if not tags:
            return pd.DataFrame(columns=["hashtag", "count"])
        s = pd.Series(tags).value_counts().head(top_n)
        return pd.DataFrame({"hashtag": s.index, "count": s.values})

    def top_posts_by_engagement(self, df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
        return (
            df.sort_values("er_per_impression_pct", ascending=False).head(n)
            .loc[:, ["Impressions", "Likes", "Comments", "Saves", "Shares", "er_per_impression_pct"]]
            .rename(columns={
                "Impressions": "Показы",
                "Likes": "Лайки",
                "Comments": "Комментарии",
                "Saves": "Сохранения",
                "Shares": "Репосты",
                "er_per_impression_pct": "ER на показ, %",
            })
            .reset_index(drop=True)
        )


def _ru_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        font=dict(family="Segoe UI, Arial, sans-serif", size=13),
        margin={"r": 20, "t": 70, "l": 20, "b": 50},
        plot_bgcolor="#fafbfc", paper_bgcolor="white",
    )
    return fig


class InstagramRealVisualizer:
    @staticmethod
    def impressions_pie(breakdown: pd.DataFrame) -> go.Figure:
        d = breakdown.copy()
        d["Источник"] = d["source"].map(lambda x: SOURCES_RU.get(x, x))
        fig = px.pie(d, names="Источник", values="impressions", hole=0.5)
        return _ru_layout(fig, "Откуда приходят показы у Instagram-аккаунта (реальные данные, 119 постов)")

    @staticmethod
    def likes_vs_impressions(df: pd.DataFrame) -> go.Figure:
        try:
            import statsmodels.api  # noqa: F401
            trend = "ols"
        except ImportError:
            trend = None
        fig = px.scatter(
            df, x="Impressions", y="Likes", size="Likes", trendline=trend,
            labels={"Impressions": "Показы", "Likes": "Лайки"},
        )
        return _ru_layout(fig, "Лайки в зависимости от показов (с линией тренда)")

    @staticmethod
    def correlation_heatmap(corr: pd.DataFrame) -> go.Figure:
        rename = {
            "Impressions": "Показы", "From Home": "Из ленты",
            "From Hashtags": "По хештегам", "From Explore": "Из «Интересного»",
            "Likes": "Лайки", "Comments": "Комментарии",
            "Saves": "Сохранения", "Shares": "Репосты",
            "Profile Visits": "Заходы на профиль", "Follows": "Подписки",
        }
        c = corr.rename(index=rename, columns=rename)
        fig = px.imshow(c, text_auto=True, color_continuous_scale="RdBu",
                        zmin=-1, zmax=1, aspect="auto")
        return _ru_layout(fig, "Связи между метриками Instagram-постов (корреляции)")

    @staticmethod
    def er_distribution(df: pd.DataFrame) -> go.Figure:
        fig = px.histogram(
            df, x="er_per_impression_pct", nbins=25,
            labels={"er_per_impression_pct": "Вовлечённость на показ (ER), %"},
        )
        return _ru_layout(fig, "Распределение вовлечённости постов")
