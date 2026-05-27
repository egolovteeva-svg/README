from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.geo import (
    DistrictDataLoader, PVZGenerator, GeoAnalyzer, VRPSolver, MoscowGeoJSONLoader,
)
from src.marketing import (
    CampaignAnalyzer, CompetitorAnalyzer, HHAnalyzer,
    InstagramRealDataAnalyzer, MarketingDataLoader,
    KaggleSMMAnalyzer, KaggleCampaignsAnalyzer,
    WBSampleAnalyzer, WBReviewsAnalyzer,
)

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)


def main() -> None:
    print(">> Загрузка районов Москвы")
    districts = DistrictDataLoader(RAW / "moscow_districts.csv").load()

    geojson_path = RAW / "moscow_districts.geojson"
    if geojson_path.exists():
        print(">> Уточняю координаты районов из реального GeoJSON")
        districts = MoscowGeoJSONLoader(geojson_path).enrich_districts(districts)
    districts.to_csv(PROC / "districts_enriched.csv", index=False)

    print(">> Генерация ПВЗ")
    pvz = PVZGenerator(districts).generate()
    pvz.to_csv(PROC / "pvz.csv", index=False)

    print(">> Гео-агрегаты и хабы")
    geo = GeoAnalyzer(districts=districts, pvz=pvz)
    geo.pvz_per_district().to_csv(PROC / "pvz_per_district.csv", index=False)
    geo.okrug_summary().to_csv(PROC / "okrug_summary.csv", index=False)
    hubs = geo.greedy_hub_locations(n_hubs=4, radius_km=8.0)
    hubs.to_csv(PROC / "hub_locations.csv", index=False)
    geo.delivery_distance_stats(hubs).to_csv(PROC / "delivery_distance.csv", index=False)

    print(">> VRP-маршруты для первого хаба (OR-Tools, лимит 8 сек)")
    if len(hubs) > 0:
        hub0 = hubs.iloc[0]
        solver = VRPSolver(
            hub_lat=float(hub0["lat"]), hub_lon=float(hub0["lon"]),
            pvz=pvz, num_vehicles=4, vehicle_capacity_boxes=80, radius_km=8.0,
        )
        result = solver.solve()
        if result is None:
            print("   ortools не установлен — пропускаю VRP")
        else:
            routes = result["routes"]
            if routes:
                pd.DataFrame(routes).to_csv(PROC / "vrp_routes.csv", index=False)
                print(f"   маршрутов: {len(routes)}, пробег: {result['total_distance_km']:.1f} км")

    print(">> Маркетинг: 12-канальный бенчмарк")
    md = MarketingDataLoader(
        channels_csv=RAW / "smm_channels.csv",
        competitors_csv=RAW / "competitor_reels.csv",
    )
    channels = md.load_channels()
    competitors = md.load_competitors()
    ca = CampaignAnalyzer(channels=channels)
    ca.channel_efficiency().to_csv(PROC / "channel_efficiency.csv", index=False)
    ca.allocate_budget(total_budget_rub=500_000).to_csv(PROC / "budget_plan.csv", index=False)
    CompetitorAnalyzer(competitors=competitors).benchmark().to_csv(PROC / "competitors_bench.csv", index=False)

    print(">> Instagram-датасет (chinmai-gudivada, 119 постов)")
    ig = InstagramRealDataAnalyzer(RAW / "instagram_real_dataset.csv")
    ig_df = ig.load()
    ig_df.to_csv(PROC / "instagram_real.csv", index=False)
    ig.impressions_sources_breakdown(ig_df).to_csv(PROC / "instagram_sources.csv", index=False)
    ig.correlation_matrix(ig_df).to_csv(PROC / "instagram_corr.csv")
    ig.hashtag_frequency(ig_df).to_csv(PROC / "instagram_hashtags.csv", index=False)

    print(">> Kaggle SMM (300K кампаний → выборка 50K)")
    if (RAW / "kaggle_social_media_ads.csv").exists():
        ksmm = KaggleSMMAnalyzer(RAW / "kaggle_social_media_ads.csv")
        ksmm_df = ksmm.load(sample_n=50_000)
        ksmm.by_channel(ksmm_df).to_csv(PROC / "kaggle_smm_by_channel.csv", index=False)
        ksmm.by_audience(ksmm_df).to_csv(PROC / "kaggle_smm_by_audience.csv", index=False)
        ksmm.by_segment(ksmm_df).to_csv(PROC / "kaggle_smm_by_segment.csv", index=False)
        ksmm_df.head(5000).to_csv(PROC / "kaggle_smm_sample.csv", index=False)

    print(">> Kaggle Marketing Campaigns (200K → выборка 50K)")
    if (RAW / "kaggle_marketing_campaigns.csv").exists():
        kmc = KaggleCampaignsAnalyzer(RAW / "kaggle_marketing_campaigns.csv")
        kmc_df = kmc.load(sample_n=50_000)
        kmc.by_campaign_type(kmc_df).to_csv(PROC / "kaggle_mc_by_type.csv", index=False)
        kmc.by_channel(kmc_df).to_csv(PROC / "kaggle_mc_by_channel.csv", index=False)
        kmc_df.head(5000).to_csv(PROC / "kaggle_mc_sample.csv", index=False)

    print(">> Wildberries: 1001 листинг с ценами и рейтингами")
    if (RAW / "wb_sample.csv").exists():
        wb = WBSampleAnalyzer(RAW / "wb_sample.csv")
        wb_df = wb.load()
        wb_df.to_csv(PROC / "wb_clean.csv", index=False)
        wb.by_category(wb_df).to_csv(PROC / "wb_by_category.csv", index=False)

    print(">> Wildberries: 20 000 реальных отзывов про подарки")
    if (RAW / "wb_gift_reviews.csv").exists():
        wbr = WBReviewsAnalyzer(RAW / "wb_gift_reviews.csv")
        wbr_df = wbr.load()
        pd.DataFrame([wbr.summary(wbr_df)]).to_csv(PROC / "wb_reviews_summary.csv", index=False)
        wbr.by_keyword(wbr_df).to_csv(PROC / "wb_reviews_by_keyword.csv", index=False)
        wbr.top_brands(wbr_df).to_csv(PROC / "wb_reviews_top_brands.csv", index=False)
        wbr_df[["category","keyword","brand","name","mark","mentions_gift","is_positive","is_negative"]].head(3000).to_csv(
            PROC / "wb_reviews_sample.csv", index=False)

    print(">> Сотрудники (Mendeley + индексация ×1.50)")
    if (RAW / "hh_vacancies_moscow.csv").exists():
        hh = HHAnalyzer(RAW / "hh_vacancies_moscow.csv")
        hh_df = hh.load()
        hh_df.to_csv(PROC / "hh_clean.csv", index=False)
        hh.by_query(hh_df).to_csv(PROC / "hh_by_query.csv", index=False)
        hh.by_experience(hh_df).to_csv(PROC / "hh_by_experience.csv", index=False)

    print("\n>> Готово. Файлы в data/processed/:")
    for f in sorted(PROC.glob("*.csv")):
        print("  -", f.name)


if __name__ == "__main__":
    main()
