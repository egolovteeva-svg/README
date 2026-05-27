from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class MarketingDataLoader:
    channels_csv: Path
    competitors_csv: Path

    def load_channels(self) -> pd.DataFrame:
        df = pd.read_csv(self.channels_csv)
        df["effective_cpc_rub"] = df.apply(
            lambda r: r["avg_cpc_rub"] if r["avg_cpc_rub"] > 0 else None,
            axis=1,
        )
        return df

    def load_competitors(self) -> pd.DataFrame:
        df = pd.read_csv(self.competitors_csv)
        df["engagement_rate_pct"] = (
            (df["avg_likes"] + df["avg_comments"] + df["avg_saves"]
             + df["avg_shares"])
            / df["followers"]
            * 100
        )
        df["cost_per_1k_views_rub"] = (
            df["price_per_post_rub"] / df["avg_views"] * 1000
        )
        return df
