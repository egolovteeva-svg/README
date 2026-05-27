from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data_loader import haversine_km


@dataclass
class GeoAnalyzer:
    districts: pd.DataFrame
    pvz: pd.DataFrame

    def pvz_per_district(self) -> pd.DataFrame:
        agg = (
            self.pvz.groupby(["district", "okrug"])
            .agg(pvz_count=("pvz_id", "count"),
                 daily_orders=("daily_orders", "sum"))
            .reset_index()
        )
        merged = self.districts.merge(agg, on=["district", "okrug"], how="left")
        merged[["pvz_count", "daily_orders"]] = merged[
            ["pvz_count", "daily_orders"]
        ].fillna(0)
        merged["pvz_per_10k_people"] = (
            merged["pvz_count"] / merged["population"] * 10000
        )
        return merged

    def okrug_summary(self) -> pd.DataFrame:
        per_district = self.pvz_per_district()
        return (
            per_district.groupby("okrug")
            .agg(
                population=("population", "sum"),
                area_km2=("area_km2", "sum"),
                pvz_count=("pvz_count", "sum"),
                daily_orders=("daily_orders", "sum"),
                avg_income_rub=("avg_income_rub", "mean"),
            )
            .reset_index()
            .assign(
                pvz_per_10k=lambda d: d["pvz_count"] / d["population"] * 10000,
                orders_per_km2=lambda d: d["daily_orders"] / d["area_km2"],
            )
            .sort_values("daily_orders", ascending=False)
        )

    def coverage_for_hub(self, hub_lat: float, hub_lon: float,
                        radius_km: float = 8.0) -> dict:
        d = haversine_km(self.pvz["lat"], self.pvz["lon"], hub_lat, hub_lon)
        mask = d <= radius_km
        return {
            "hub_lat": hub_lat,
            "hub_lon": hub_lon,
            "radius_km": radius_km,
            "pvz_in_radius": int(mask.sum()),
            "daily_orders_covered": int(self.pvz.loc[mask, "daily_orders"].sum()),
            "share_of_total_orders": float(
                self.pvz.loc[mask, "daily_orders"].sum()
                / self.pvz["daily_orders"].sum()
            ),
        }

    def greedy_hub_locations(self, n_hubs: int = 4,
                             radius_km: float = 8.0) -> pd.DataFrame:
        candidates = self.districts[["district", "okrug", "lat", "lon"]].copy()
        remaining = self.pvz.copy()
        chosen: list[dict] = []

        for _ in range(n_hubs):
            best = None
            best_orders = -1
            for _, row in candidates.iterrows():
                d = haversine_km(
                    remaining["lat"], remaining["lon"], row["lat"], row["lon"]
                )
                covered = remaining.loc[d <= radius_km, "daily_orders"].sum()
                if covered > best_orders:
                    best_orders = int(covered)
                    best = row
            if best is None or best_orders <= 0:
                break
            chosen.append(
                {
                    "hub_district": best["district"],
                    "okrug": best["okrug"],
                    "lat": best["lat"],
                    "lon": best["lon"],
                    "covered_orders": best_orders,
                }
            )
            d = haversine_km(
                remaining["lat"], remaining["lon"], best["lat"], best["lon"]
            )
            remaining = remaining.loc[d > radius_km].copy()
            candidates = candidates.loc[
                candidates["district"] != best["district"]
            ]
        return pd.DataFrame(chosen)

    def delivery_distance_stats(self, hubs: pd.DataFrame) -> pd.DataFrame:
        results: list[dict] = []
        for _, pvz in self.pvz.iterrows():
            d = haversine_km(hubs["lat"], hubs["lon"], pvz["lat"], pvz["lon"])
            idx = int(np.argmin(d))
            results.append(
                {
                    "pvz_id": pvz["pvz_id"],
                    "marketplace": pvz["marketplace"],
                    "district": pvz["district"],
                    "nearest_hub": hubs.iloc[idx]["hub_district"],
                    "distance_km": round(float(d[idx]), 2),
                    "daily_orders": pvz["daily_orders"],
                }
            )
        return pd.DataFrame(results)
