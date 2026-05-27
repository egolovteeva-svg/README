from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.labels import POSITION_RU, SCHEDULE_RU, translate


@dataclass
class HHAnalyzer:
    csv_path: Path

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        df["salary_from"] = pd.to_numeric(df["salary_from"], errors="coerce")
        df["salary_to"] = pd.to_numeric(df["salary_to"], errors="coerce")
        df["salary_mid"] = df[["salary_from", "salary_to"]].mean(axis=1)
        df = df[df["salary_currency"].isin(["RUR", np.nan])].copy()
        return df

    def by_query(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby("query").agg(
                vacancies=("name", "count"),
                avg_salary_from=("salary_from", "mean"),
                avg_salary_to=("salary_to", "mean"),
                median_salary_mid=("salary_mid", "median"),
                p25_salary_mid=("salary_mid", lambda s: s.quantile(0.25)),
                p75_salary_mid=("salary_mid", lambda s: s.quantile(0.75)),
            ).round(0).reset_index().sort_values("median_salary_mid", ascending=False)
        )

    def by_experience(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby("experience").agg(
                vacancies=("name", "count"),
                median_salary=("salary_mid", "median"),
            ).round(0).reset_index().sort_values("median_salary", ascending=False)
        )

    def total_team_cost(self, df: pd.DataFrame, positions: dict[str, int],
                        benefits_multiplier: float = 1.30) -> dict:
        by_q = self.by_query(df).set_index("query")
        breakdown: list[dict] = []
        total_gross = 0.0
        for q, n in positions.items():
            if q not in by_q.index:
                continue
            med = float(by_q.loc[q, "median_salary_mid"])
            with_benefits = med * n * benefits_multiplier
            total_gross += with_benefits
            breakdown.append({
                "Позиция": POSITION_RU.get(q, q),
                "Кол-во человек": n,
                "Медианная ЗП, ₽": int(med),
                "Затраты в месяц, ₽": int(with_benefits),
            })
        return {
            "breakdown": pd.DataFrame(breakdown),
            "monthly_total_rub": round(total_gross, 0),
            "annual_total_rub": round(total_gross * 12, 0),
            "benefits_multiplier": benefits_multiplier,
        }


def _ru_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        font=dict(family="Segoe UI, Arial, sans-serif", size=13),
        margin={"r": 20, "t": 70, "l": 20, "b": 50},
        plot_bgcolor="#fafbfc", paper_bgcolor="white",
    )
    return fig


class HHVisualizer:
    @staticmethod
    def salary_box(df: pd.DataFrame) -> go.Figure:
        d = df.dropna(subset=["salary_mid"]).copy()
        d["Позиция"] = translate(d["query"], POSITION_RU)
        fig = px.box(
            d, x="Позиция", y="salary_mid", color="Позиция",
            points="outliers",
            labels={"salary_mid": "Зарплата, руб (середина вилки)"},
        )
        fig.update_layout(showlegend=False)
        return _ru_layout(fig, "Распределение зарплат по позициям — Москва, 2026 (Mendeley, индексация ×1.5)")

    @staticmethod
    def median_bar(by_query: pd.DataFrame) -> go.Figure:
        d = by_query.copy()
        d["Позиция"] = translate(d["query"], POSITION_RU)
        fig = px.bar(
            d.sort_values("median_salary_mid"),
            x="median_salary_mid", y="Позиция", orientation="h",
            color="vacancies", color_continuous_scale="Viridis",
            labels={"median_salary_mid": "Медианная зарплата, руб",
                    "vacancies": "Кол-во вакансий"},
        )
        return _ru_layout(fig, "Медианная зарплата по позициям (Москва)")

    @staticmethod
    def schedule_pie(df: pd.DataFrame) -> go.Figure:
        d = df["schedule"].astype(str).map(lambda x: SCHEDULE_RU.get(x, x))
        counts = d.value_counts().reset_index()
        counts.columns = ["График работы", "Кол-во"]
        fig = px.pie(counts, names="График работы", values="Кол-во", hole=0.45)
        return _ru_layout(fig, "Графики работы в найденных вакансиях")
