from datetime import date, timedelta

from app.prompts.personas import PERSONA_OPTIONS

HORIZON_DAYS = 90

_ZONE_LABEL_TO_KEY = {item["label"]: item["key"] for item in PERSONA_OPTIONS["zones"]}

# tags: zone keys this node is allowed to hint for. Empty = never auto-hint.
_SEASONAL = [
    (1, 1, 1, 1, "元旦", "全国", "life", "新年第一更、年度愿望"),
    (2, 14, 2, 14, "情人节", "线下门店", "life,food,fashion", "约会探店、礼物测评"),
    (3, 8, 3, 8, "妇女节", "全国", "fashion,life", "女性向体验、美妆礼盒"),
    (4, 4, 4, 6, "清明小长假", "出行城市", "travel,life,auto", "短途出行、城市漫游"),
    (5, 1, 5, 5, "劳动节假期", "景区 / 商场", "travel,food,life", "人从众实地、值不值得出门"),
    (5, 20, 5, 20, "520", "线上 + 线下", "life,fashion,food", "告白礼物、探店"),
    (6, 1, 6, 1, "儿童节", "商场 / 乐园", "animal,life", "亲子场、宠物友好空间"),
    (6, 18, 6, 20, "618 大促", "线上", "tech,fashion,food,auto", "购物车开箱、回购避坑"),
    (6, 21, 6, 22, "毕业季", "高校城市", "life,travel,cine", "毕业旅行、城市漫游"),
    (8, 8, 8, 8, "七夕", "全国", "life,food,fashion", "约会路线、礼物实测"),
    (9, 1, 9, 15, "开学季", "校园 / 数码", "tech,knowledge,life", "开学装备、学习设备"),
    (9, 10, 9, 12, "中秋", "全国", "food,life", "礼盒测评、探店"),
    (10, 1, 10, 7, "国庆黄金周", "热门城市", "travel,food,life,auto", "出行体验、展会扎堆"),
    (10, 31, 10, 31, "万圣节", "商场 / 街区", "fashion,cine,life", "装扮、快闪、夜场"),
    (11, 11, 11, 11, "双11", "线上", "tech,fashion,food,auto", "预售开箱、价格追踪"),
    (12, 12, 12, 12, "双12", "线上", "tech,fashion,food", "年终补单、爱用物"),
    (12, 24, 12, 25, "圣诞节", "商场 / 街区", "life,food,fashion,music", "圣诞市集、氛围探店"),
]


def capture_window(today: date | None = None) -> tuple[date, date]:
    today = today or date.today()
    return today, today + timedelta(days=HORIZON_DAYS)


def overlaps_window(start_date: str, end_date: str, today: date | None = None) -> bool:
    today, until = capture_window(today)
    start = _parse(start_date)
    if start is None:
        return False
    end = _parse(end_date) or start
    return start <= until and end >= today


def persona_zone_key(persona) -> str:
    zone = (getattr(persona, "zone", "") or "").strip()
    if zone in _ZONE_LABEL_TO_KEY:
        return _ZONE_LABEL_TO_KEY[zone]
    for label, key in _ZONE_LABEL_TO_KEY.items():
        if label in zone or key in zone.lower():
            return key
    return ""


def seasonal_hints_for_persona(persona, today: date | None = None) -> list[dict]:
    """Only season nodes that can reasonably map to this persona's zone."""
    zone_key = persona_zone_key(persona)
    today, until = capture_window(today)
    years = {today.year, until.year}
    items: list[dict] = []
    for year in sorted(years):
        for m1, d1, m2, d2, title, location, tags, angle in _SEASONAL:
            tag_set = {item.strip() for item in tags.split(",") if item.strip()}
            if zone_key and zone_key not in tag_set:
                continue
            try:
                start = date(year, m1, d1)
                end = date(year, m2, d2)
            except ValueError:
                continue
            if start > until or end < today:
                continue
            items.append(
                {
                    "title": title,
                    "start_date": start.isoformat(),
                    "end_date": end.isoformat(),
                    "location": location,
                    "angle": angle,
                }
            )
    items.sort(key=lambda row: row["start_date"])
    return items


def _parse(value: str) -> date | None:
    text = (value or "").strip()[:10]
    if len(text) < 10:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None
