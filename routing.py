from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from .data_loader import haversine_km


@dataclass
class VRPSolver:
    hub_lat: float
    hub_lon: float
    pvz: pd.DataFrame
    num_vehicles: int = 4
    vehicle_capacity_boxes: int = 80
    radius_km: float = 8.0
    max_stops: int = 60
    time_limit_sec: int = 8

    def _stops_in_zone(self) -> pd.DataFrame:
        d = haversine_km(self.pvz["lat"], self.pvz["lon"], self.hub_lat, self.hub_lon)
        stops = self.pvz.loc[d <= self.radius_km].copy()
        stops["distance_from_hub_km"] = d[d <= self.radius_km]
        stops = stops.sort_values("daily_orders", ascending=False).head(self.max_stops)
        return stops.reset_index(drop=True)

    def _build_distance_matrix(self, stops: pd.DataFrame) -> np.ndarray:
        lats = np.concatenate([[self.hub_lat], stops["lat"].to_numpy()])
        lons = np.concatenate([[self.hub_lon], stops["lon"].to_numpy()])
        n = len(lats)
        mat = np.zeros((n, n))
        for i in range(n):
            mat[i, :] = haversine_km(lats, lons, lats[i], lons[i])
        return (mat * 100).astype(int)

    def _demands(self, stops: pd.DataFrame) -> list[int]:
        return [0] + [int(max(1, round(o / 15))) for o in stops["daily_orders"]]

    def solve(self) -> Optional[dict]:
        try:
            from ortools.constraint_solver import pywrapcp, routing_enums_pb2
        except ImportError:
            return None

        stops = self._stops_in_zone()
        if len(stops) == 0:
            return {"routes": [], "total_distance_km": 0.0, "stops": stops}

        distance_matrix = self._build_distance_matrix(stops)
        demands = self._demands(stops)

        manager = pywrapcp.RoutingIndexManager(
            len(distance_matrix), self.num_vehicles, 0
        )
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            return int(distance_matrix[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)])

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        def demand_callback(from_index):
            return demands[manager.IndexToNode(from_index)]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index, 0,
            [self.vehicle_capacity_boxes] * self.num_vehicles, True, "Capacity",
        )

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.time_limit.seconds = self.time_limit_sec
        solution = routing.SolveWithParameters(search_parameters)
        if solution is None:
            return {"routes": [], "total_distance_km": 0.0, "stops": stops}

        routes: list[dict] = []
        total_distance = 0
        for vid in range(self.num_vehicles):
            index = routing.Start(vid)
            route_nodes: list[int] = []
            route_load = 0
            route_distance = 0
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                route_nodes.append(node)
                route_load += demands[node]
                prev = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(prev, index, vid)
            route_nodes.append(manager.IndexToNode(index))
            if len(route_nodes) > 2:
                routes.append({
                    "vehicle": vid, "stops": route_nodes,
                    "load_boxes": route_load,
                    "distance_km": route_distance / 100.0,
                })
                total_distance += route_distance
        return {
            "routes": routes,
            "total_distance_km": total_distance / 100.0,
            "stops": stops,
        }
