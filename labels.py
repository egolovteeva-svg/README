POSITION_RU = {
    "marketing": "Маркетолог",
    "smm": "SMM-специалист",
    "targeting": "Таргетолог",
    "gift_packer": "Упаковщик подарков",
    "courier": "Курьер",
    "marketplace_manager": "Менеджер маркетплейсов",
}

CHANNEL_RU = {
    "Facebook": "Facebook (зарубежный)",
    "Instagram": "Instagram",
    "Twitter": "Twitter / X",
    "Pinterest": "Pinterest",
    "YouTube": "YouTube",
    "Email": "Email-рассылка",
    "Google Ads": "Google Ads",
    "Website": "Сайт / прямой трафик",
}

CAMPAIGN_TYPE_RU = {
    "Email": "Email-маркетинг",
    "Search": "Поисковая реклама",
    "Display": "Медийная реклама",
    "Influencer": "Инфлюенсеры",
    "Social Media": "Социальные сети",
}

AUDIENCE_RU = {
    "All Ages": "Все возрасты",
    "Men 18-24": "Мужчины 18-24",
    "Men 25-34": "Мужчины 25-34",
    "Men 35-44": "Мужчины 35-44",
    "Men 45-60": "Мужчины 45-60",
    "Women 18-24": "Женщины 18-24",
    "Women 25-34": "Женщины 25-34",
    "Women 35-44": "Женщины 35-44",
    "Women 45-60": "Женщины 45-60",
}

SEGMENT_RU = {
    "Technology": "Любители техники и гаджетов",
    "Home": "Дом и интерьер",
    "Fashion": "Мода и стиль",
    "Health": "Здоровье и красота",
    "Food": "Еда и напитки",
    "Foodies": "Любители еды",
    "Tech Enthusiasts": "Любители техники",
    "Outdoor Adventurers": "Активный отдых",
    "Health & Wellness": "ЗОЖ и здоровье",
    "Fashionistas": "Любители моды",
}

SCHEDULE_RU = {
    "full_day": "Полный день",
    "fullDay": "Полный день",
    "flexible": "Гибкий график",
    "remote": "Удалённая работа",
    "shift": "Сменный график",
    "fly_in_fly_out": "Вахтовый метод",
}

EMPLOYMENT_RU = {
    "full": "Полная занятость",
    "part": "Частичная занятость",
    "probation": "Стажировка",
    "project": "Проектная работа",
}

NICHE_RU = {
    "gift_wrapping": "Подарочная упаковка",
    "gift_delivery": "Доставка подарков",
    "gift_marketplace": "Маркетплейс подарков",
    "seasonal_gifts": "Сезонные подарки",
    "premium_wrapping": "Премиум-упаковка",
}

MARKETPLACE_RU = {
    "Ozon": "Ozon",
    "Wildberries": "Wildberries",
    "Lamoda": "Lamoda",
}


def translate(series, mapping):
    return series.map(lambda x: mapping.get(str(x), str(x)))
