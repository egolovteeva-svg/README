from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass
class DistrictDataLoader:
    csv_path: Path

    def load(self) -> pd.DataFrame:
        df = pd.read_csv(self.csv_path)
        numeric_cols = ["population", "area_km2", "avg_income_rub", "lat", "lon"]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["density_per_km2"] = df["population"] / df["area_km2"]
        return df


class PVZGenerator:
    MARKETPLACES = ("Ozon", "Wildberries", "Lamoda")

    def __init__(self, districts: pd.DataFrame, seed: int = 42) -> None:
        self.districts = districts
        self.rng = np.random.default_rng(seed)

    def _count_for_district(self, population: float) -> int:
        base = max(1, int(round(population / 8000)))
        noise = self.rng.integers(-1, 2)
        return max(1, base + noise)

    def _jitter(self, value: float, scale: float = 0.012) -> float:
        return float(value + self.rng.normal(0, scale))

    def generate(self) -> pd.DataFrame:
        rows: list[dict] = []
        for _, row in self.districts.iterrows():
            n = self._count_for_district(row["population"])
            for i in range(n):
                marketplace = self.rng.choice(
                    self.MARKETPLACES, p=[0.45, 0.40, 0.15]
                )
                rows.append(
                    {
                        "pvz_id": f"{row['district'][:3].upper()}-{i + 1:03d}",
                        "marketplace": marketplace,
                        "district": row["district"],
                        "okrug": row["okrug"],
                        "lat": self._jitter(row["lat"]),
                        "lon": self._jitter(row["lon"]),
                        "daily_orders": int(
                            self.rng.normal(loc=120, scale=35)
                        ),
                    }
                )
        df = pd.DataFrame(rows)
        df["daily_orders"] = df["daily_orders"].clip(lower=20)
        return df


def haversine_km(lat1: Iterable[float], lon1: Iterable[float],
                 lat2: float, lon2: float) -> np.ndarray:
    lat1 = np.radians(np.asarray(lat1, dtype=float))
    lon1 = np.radians(np.asarray(lon1, dtype=float))
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))
