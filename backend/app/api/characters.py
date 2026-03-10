import json
import random
from collections import defaultdict
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Query

router = APIRouter()

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
CHARACTERS_FILE = DATA_DIR / "characters.json"

_cached_characters = None

RACE_GROUPS = {
    "人类": ["人类"],
    "兽人": ["兽人", "兽人（凯茨莱茵家族）", "兽人（猫）", "兽人（蝙蝠人）", "兽人（巴螺迦修那的后裔）", "兽人（豹猫人）", "兽人（牛）", "兽人（鹿）"],
    "仙人/半仙": ["仙人", "仙人（天使）", "半仙", "半仙（麒麟）", "元素生命（仙人）"],
    "妖怪": ["妖怪（天狗）", "妖怪（猫又）", "妖怪（鬼族）", "妖怪（仙狐）", "妖怪（食梦貘）", "妖精"],
    "魔神/元素": ["魔神", "魔神（元素精灵）", "魔神/人偶", "元素生物（水龙王）", "草木化身", "草木化身（", "月神"],
    "造物": ["炼金造物", "炼金造物（龙）", "人偶", "机器人"],
    "其他": ["僵尸", "长生种（未知）", "美露莘"],
}
RACE_OVERRIDE_BY_NAME = {"玛薇卡": "魔神/元素"}
RACE_RAW_TO_GROUP = {r: g for g, raws in RACE_GROUPS.items() for r in raws}


def load_characters():
    global _cached_characters
    if _cached_characters is not None:
        return _cached_characters
    if not CHARACTERS_FILE.exists():
        _cached_characters = []
        return []
    with open(CHARACTERS_FILE, encoding="utf-8") as f:
        _cached_characters = json.load(f)
    return _cached_characters


@router.get("/characters")
def list_characters(
    element: str | None = Query(None, description="元素：火/水/风/雷/草/岩/冰"),
    weapon: str | None = Query(None, description="武器类型"),
    rarity: int | None = Query(None, ge=4, le=5, description="稀有度 4 或 5"),
    body_type: str | None = Query(None, description="体型：少女/成女/少年/成男"),
    region: str | None = Query(None, description="地区：蒙德/璃月/稻妻/须弥/枫丹/纳塔/至冬/坎瑞亚/其他"),
    race: str | None = Query(None, description="种族（首表字段），如 人类/丘丘人/龙等"),
    gender: str | None = Query(None, description="性别（首表字段），如 男/女/其他"),
    zodiac: str | None = Query(None, description="星座"),
    month: int | None = Query(None, ge=1, le=12, description="生日月份"),
    q: str | None = Query(None, description="全文搜索"),
):
    chars = load_characters()
    result = []
    for c in chars:
        if element and (c.get("element") or "").find(element) < 0:
            continue
        if weapon and (c.get("weapon") or "").find(weapon) < 0:
            continue
        if rarity is not None and c.get("rarity") != rarity:
            continue
        if body_type and (c.get("body_type") or "") != body_type:
            continue
        if region and (c.get("region") or "") != region:
            continue
        stats = c.get("stats") or {}
        if race:
            name = c.get("name") or ""
            group = RACE_OVERRIDE_BY_NAME.get(name)
            if group is None:
                raw = (stats.get("种族") or "").strip()
                group = RACE_RAW_TO_GROUP.get(raw, "其他") if raw else ""
            if group != race:
                continue
        if gender and (stats.get("性别") or "") != gender:
            continue
        if zodiac and (c.get("zodiac") or "") != zodiac:
            continue
        if month is not None:
            bp = c.get("birthday_parsed") or {}
            if bp.get("month") != month:
                continue
        if q:
            ql = q.lower().strip()
            st = (c.get("searchable_text") or "").lower()
            if ql not in st and ql not in (c.get("name") or "").lower():
                continue
        result.append(c)
    return result


@router.get("/characters/filter-options")
def get_filter_options():
    """返回种族（合并后）、性别的可选值"""
    chars = load_characters()
    race_set = set()
    gender_set = set()
    for c in chars:
        name = c.get("name") or ""
        group = RACE_OVERRIDE_BY_NAME.get(name)
        if group is not None:
            race_set.add(group)
        else:
            st = c.get("stats") or {}
            raw = (st.get("种族") or "").strip()
            if raw:
                race_set.add(RACE_RAW_TO_GROUP.get(raw, "其他"))
        if st.get("性别"):
            gender_set.add(st["性别"])
    return {"race": sorted(race_set), "gender": sorted(gender_set)}


@router.get("/characters/stats")
def get_stats():
    """聚合统计：元素、武器、稀有度、地区、星座、体型分布"""
    chars = load_characters()
    stats = {
        "total": len(chars),
        "by_element": defaultdict(int),
        "by_weapon": defaultdict(int),
        "by_rarity": defaultdict(int),
        "by_region": defaultdict(int),
        "by_zodiac": defaultdict(int),
        "by_body_type": defaultdict(int),
        "by_birthday_month": defaultdict(int),
    }
    for c in chars:
        if c.get("element"):
            stats["by_element"][c["element"]] += 1
        if c.get("weapon"):
            stats["by_weapon"][c["weapon"]] += 1
        if c.get("rarity"):
            stats["by_rarity"][str(c["rarity"])] += 1
        if c.get("region"):
            stats["by_region"][c["region"]] += 1
        if c.get("zodiac"):
            stats["by_zodiac"][c["zodiac"]] += 1
        if c.get("body_type"):
            stats["by_body_type"][c["body_type"]] += 1
        bp = c.get("birthday_parsed") or {}
        if bp.get("month"):
            stats["by_birthday_month"][str(bp["month"])] += 1
    return {k: dict(v) if isinstance(v, defaultdict) else v for k, v in stats.items()}


@router.get("/characters/random")
def random_character():
    chars = load_characters()
    if not chars:
        return None
    return random.choice(chars)


@router.get("/characters/today")
def today_character():
    """今日推荐：按日期 hash 固定轮播"""
    chars = load_characters()
    if not chars:
        return None
    today = date.today()
    seed = today.year * 10000 + today.month * 100 + today.day
    idx = seed % len(chars)
    return chars[idx]


@router.get("/characters/birthday-calendar")
def birthday_calendar():
    """按月份返回生日列表 { "1": [...], "2": [...], ... }"""
    chars = load_characters()
    by_month = defaultdict(list)
    for c in chars:
        bp = c.get("birthday_parsed") or {}
        m = bp.get("month")
        if m:
            by_month[str(m)].append(
                {
                    "character_id": c.get("character_id"),
                    "name": c.get("name"),
                    "birthday": c.get("birthday"),
                    "day": bp.get("day"),
                    "image_url": c.get("image_url") or (c.get("portraits") or {}).get("立绘"),
                }
            )
    for k in by_month:
        by_month[k].sort(key=lambda x: x["day"])
    return dict(by_month)


@router.get("/characters/{character_id}")
def get_character(character_id: str):
    chars = load_characters()
    for c in chars:
        if c.get("character_id") == character_id:
            return c
    return None
