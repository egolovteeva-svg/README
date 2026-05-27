from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class CampaignAnalyzer:
    channels: pd.DataFrame
    avg_check_rub: float = 1200.0
    conversion_pct: float = 1.8

    def channel_efficiency(self) -> pd.DataFrame:
        df = self.channels.copy()
        df["cpv_rub"] = df["avg_cpc_rub"].replace(0, np.nan)
        df["expected_revenue_per_post"] = (
            df["reach_per_post"]
            * (df["avg_engagement_rate_pct"] / 100)
            * (self.conversion_pct / 100)
            * self.avg_check_rub
        )
        df["roas"] = df["expected_revenue_per_post"] / df["avg_post_cost_rub"]
        df["efficiency_rank"] = df["roas"].rank(ascending=False).astype(int)
        return df.sort_values("roas", ascending=False)

    def allocate_budget(self, total_budget_rub: float = 500_000) -> pd.DataFrame:
        eff = self.channel_efficiency().head(6).copy()
        weights = eff["roas"].clip(lower=0)
        eff["budget_share_pct"] = (weights / weights.sum() * 100).round(1)
        eff["budget_rub"] = (
            (weights / weights.sum()) * total_budget_rub
        ).round(-2)
        eff["expected_posts"] = (eff["budget_rub"] / eff["avg_post_cost_rub"]).round(1)
        eff["expected_reach"] = (eff["expected_posts"] * eff["reach_per_post"]).round(-2)
        eff["expected_orders"] = (
            eff["expected_reach"]
            * (eff["avg_engagement_rate_pct"] / 100)
            * (self.conversion_pct / 100)
        ).round(0)
        eff["expected_revenue_rub"] = (
            eff["expected_orders"] * self.avg_check_rub
        ).round(-2)
        return eff[
            [
                "channel",
                "roas",
                "budget_share_pct",
                "budget_rub",
                "expected_posts",
                "expected_reach",
                "expected_orders",
                "expected_revenue_rub",
            ]
        ]

    def funnel_kpis(self, budget_rub: float = 500_000) -> dict:
        plan = self.allocate_budget(budget_rub)
        total_reach = plan["expected_reach"].sum()
        total_orders = plan["expected_orders"].sum()
        total_revenue = plan["expected_revenue_rub"].sum()
        return {
            "total_budget_rub": budget_rub,
            "total_reach": int(total_reach),
            "total_orders": int(total_orders),
            "total_revenue_rub": float(total_revenue),
            "blended_roas": round(total_revenue / budget_rub, 2),
            "cac_rub": round(budget_rub / max(total_orders, 1), 2),
        }


@dataclass
class CompetitorAnalyzer:
    competitors: pd.DataFrame

    def benchmark(self) -> pd.DataFrame:
        df = self.competitors.copy()
        df["er_per_follower"] = df["engagement_rate_pct"]
        return df.sort_values("er_per_follower", ascending=False)

    def er_difference_test(self, niche_a: str = "gift_wrapping",
                           niche_b: str = "gift_delivery") -> dict:
        a = self.competitors.loc[
            self.competitors["niche"] == niche_a, "engagement_rate_pct"
        ]
        b = self.competitors.loc[
            self.competitors["niche"] == niche_b, "engagement_rate_pct"
        ]
        if len(a) < 2 or len(b) < 2:
            return {"niche_a": niche_a, "niche_b": niche_b,
                    "note": "слишком мало наблюдений"}
        t_stat, p_value = stats.ttest_ind(a, b, equal_var=False)
        return {
            "niche_a": niche_a,
            "niche_b": niche_b,
            "mean_a": round(float(a.mean()), 2),
            "mean_b": round(float(b.mean()), 2),
            "t_stat": round(float(t_stat), 3),
            "p_value": round(float(p_value), 4),
            "significant_at_5pct": bool(p_value < 0.05),
        }
