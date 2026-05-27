from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _ru_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        font=dict(family="Segoe UI, Arial, sans-serif", size=13),
        margin={"r": 20, "t": 70, "l": 20, "b": 50},
        plot_bgcolor="#fafbfc", paper_bgcolor="white",
    )
    return fig


@dataclass
class WBSampleAnalyzer:
    csv_path: Path

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        df["initial_price"] = pd.to_numeric(df["initial_price"], errors="coerce")
        df["final_price"] = pd.to_numeric(df["final_price"], errors="coerce")
        df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
        df["review_count"] = pd.to_numeric(df["review_count"], errors="coerce")
        df["discount_pct"] = (
            (df["initial_price"] - df["final_price"]) / df["initial_price"] * 100
        ).round(1)
        df["top_category"] = df["breadcrumbs"].apply(self._top_category)
        return df

    @staticmethod
    def _top_category(s: str) -> str:
        try:
            parts = ast.literal_eval(s) if isinstance(s, str) else []
            return parts[0] if parts else ""
        except Exception:
            return ""

    def by_category(self, df: pd.DataFrame, top_n: int = 12) -> pd.DataFrame:
        d = df[df["top_category"] != ""]
        out = (
            d.groupby("top_category").agg(
                товаров=("sku", "count"),
                средний_чек=("final_price", "mean"),
                медианный_чек=("final_price", "median"),
                средний_рейтинг=("rating", "mean"),
                средняя_скидка_pct=("discount_pct", "mean"),
                всего_отзывов=("review_count", "sum"),
            ).round(1).reset_index().sort_values("товаров", ascending=False)
        )
        return out.head(top_n)


@dataclass
class WBReviewsAnalyzer:
    csv_path: Path

    POSITIVE_KEYWORDS = ["подари", "понравил", "хорош", "красив", "качествен", "рекоменду"]
    NEGATIVE_KEYWORDS = ["не подош", "плох", "разочарова", "ужасн", "брак", "сломал", "не соответств"]
    GIFT_RELATED = ["подарок", "подарк", "сюрприз", "поздравлен", "праздн", "подарочн"]

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        df["mark"] = pd.to_numeric(df["mark"], errors="coerce")
        df["text_lower"] = df["text"].fillna("").astype(str).str.lower()
        df["is_positive"] = df["text_lower"].apply(
            lambda t: any(k in t for k in self.POSITIVE_KEYWORDS)
        )
        df["is_negative"] = df["text_lower"].apply(
            lambda t: any(k in t for k in self.NEGATIVE_KEYWORDS)
        )
        df["mentions_gift"] = df["text_lower"].apply(
            lambda t: any(k in t for k in self.GIFT_RELATED)
        )
        return df

    def summary(self, df: pd.DataFrame) -> dict:
        return {
            "всего_отзывов": int(len(df)),
            "упомянули_подарок": int(df["mentions_gift"].sum()),
            "позитивных": int(df["is_positive"].sum()),
            "негативных": int(df["is_negative"].sum()),
            "средняя_оценка": round(float(df["mark"].mean()), 2),
            "доля_5_звёзд_pct": round(float((df["mark"] == 5).mean() * 100), 1),
        }

    def by_keyword(self, df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
        return (
            df[df["keyword"].notna()]
            .groupby("keyword").agg(
                отзывов=("text", "count"),
                средняя_оценка=("mark", "mean"),
                доля_про_подарок_pct=("mentions_gift", lambda s: round(s.mean() * 100, 1)),
            ).round(2).reset_index().sort_values("отзывов", ascending=False).head(top_n)
        )

    def top_brands(self, df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
        return (
            df[df["brand"].notna()]
            .groupby("brand").agg(
                отзывов=("text", "count"),
                средняя_оценка=("mark", "mean"),
            ).round(2).reset_index().sort_values("отзывов", ascending=False).head(top_n)
        )


class WBVisualizer:
    @staticmethod
    def category_prices_bar(by_cat: pd.DataFrame) -> go.Figure:
        d = by_cat.copy()
        fig = px.bar(
            d.sort_values("средний_чек"),
            x="средний_чек", y="top_category", orientation="h",
            color="средний_рейтинг", color_continuous_scale="RdYlGn",
            labels={"средний_чек": "Средний чек, ₽",
                    "top_category": "Категория WB",
                    "средний_рейтинг": "Средний рейтинг"},
            hover_data={"товаров": True, "медианный_чек": True,
                        "всего_отзывов": True, "средняя_скидка_pct": True},
        )
        return _ru_layout(fig, "Категории Wildberries: средний чек и рейтинг (1001 листинг)")

    @staticmethod
    def rating_distribution(df: pd.DataFrame) -> go.Figure:
        fig = px.histogram(
            df.dropna(subset=["mark"]), x="mark", nbins=5,
            color_discrete_sequence=["#4a90e2"],
            labels={"mark": "Оценка отзыва (1-5)"},
        )
        return _ru_layout(fig, "Распределение оценок в 20 000 реальных отзывов покупателей WB")

    @staticmethod
    def keyword_bar(by_keyword: pd.DataFrame) -> go.Figure:
        fig = px.bar(
            by_keyword.sort_values("отзывов"),
            x="отзывов", y="keyword", orientation="h",
            color="доля_про_подарок_pct", color_continuous_scale="Oranges",
            labels={"отзывов": "Кол-во отзывов",
                    "keyword": "Категория",
                    "доля_про_подарок_pct": "% отзывов с темой подарка"},
        )
        return _ru_layout(fig, "Топ категорий товаров по числу отзывов про подарки")
