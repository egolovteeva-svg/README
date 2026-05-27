from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass
class MoscowGeoJSONLoader:
    geojson_path: Path

    def load_raw(self) -> dict[str, Any]:
        with open(self.geojson_path, encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _flatten_coords(geometry: dict) -> list[tuple[float, float]]:
        t = geometry["type"]
        coords = geometry["coordinates"]
        flat: list[tuple[float, float]] = []
        if t == "Polygon":
            for ring in coords:
                for pt in ring:
                    flat.append((pt[1], pt[0]))
        elif t == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    for pt in ring:
                        flat.append((pt[1], pt[0]))
        return flat

    def centroids(self) -> pd.DataFrame:
        gj = self.load_raw()
        rows: list[dict] = []
        for feat in gj["features"]:
            name = (feat.get("properties") or {}).get("district", "")
            clean = name.replace("район ", "").strip()
            pts = self._flatten_coords(feat["geometry"])
            if not pts:
                continue
            lat = sum(p[0] for p in pts) / len(pts)
            lon = sum(p[1] for p in pts) / len(pts)
            rows.append({"district": clean, "lat": lat, "lon": lon})
        return pd.DataFrame(rows)

    def enrich_districts(self, base: pd.DataFrame) -> pd.DataFrame:
        cent = self.centroids().set_index("district")
        out = base.copy()
        for i, row in out.iterrows():
            if row["district"] in cent.index:
                out.at[i, "lat"] = float(cent.loc[row["district"], "lat"])
                out.at[i, "lon"] = float(cent.loc[row["district"], "lon"])
        return out
