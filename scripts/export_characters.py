"""
从 MongoDB 导出角色数据为 JSON，并添加增强字段：
- birthday_parsed: { month, day }
- zodiac: 星座
- region: 所属地区（蒙德/璃月/稻妻/须弥/枫丹）
- searchable_text: 全文检索用
"""
import json
import os
import re
from pathlib import Path

try:
    from pymongo import MongoClient
except ImportError:
    MongoClient = None

# 星座日期范围（月-日）
ZODIAC_RANGES = [
    (1, 20, 2, 18, "水瓶座"),
    (2, 19, 3, 20, "双鱼座"),
    (3, 21, 4, 19, "白羊座"),
    (4, 20, 5, 20, "金牛座"),
    (5, 21, 6, 21, "双子座"),
    (6, 22, 7, 22, "巨蟹座"),
    (7, 23, 8, 22, "狮子座"),
    (8, 23, 9, 22, "处女座"),
    (9, 23, 10, 23, "天秤座"),
    (10, 24, 11, 22, "天蝎座"),
    (11, 23, 12, 21, "射手座"),
    (12, 22, 1, 19, "摩羯座"),
]

# 地区关键词：从「所属地区」「出身地区」等字段匹配
REGION_KEYWORDS = {
    "蒙德": ["蒙德"],
    "璃月": ["璃月"],
    "稻妻": ["稻妻"],
    "须弥": ["须弥"],
    "枫丹": ["枫丹"],
    "纳塔": ["纳塔"],
    "至冬": ["至冬"],
    "坎瑞亚": ["坎瑞亚"],
    "其他": ["其他"],
}

# 所属组织 -> 地区（wiki 表格常只有「所属」无「所属地区」，用此补全）
AFFILIATION_TO_REGION = {
    "西风骑士团": "蒙德", "西风教会": "蒙德", "奔狼岭": "蒙德", "猫尾酒馆": "蒙德",
    "璃月七星": "璃月", "飞云商会": "璃月", "万民堂": "璃月", "不卜庐": "璃月", "天衡方士": "璃月", "璃月港": "璃月",
    "社奉行": "稻妻", "天领奉行": "稻妻", "海祇岛": "稻妻", "荒泷派": "稻妻", "终末番": "稻妻",
    "须弥教令院": "须弥", "镀金旅团": "须弥", "化城郭": "须弥", "阿如村": "须弥", "缄默之殿": "须弥",
    "枫丹廷": "枫丹", "梅洛彼得堡": "枫丹", "布法蒂公馆": "枫丹", "执灯人": "枫丹", "秘闻馆": "枫丹",
    "愚人众": "至冬", "至冬": "至冬",
    "冒险家协会": "", "南十字船队": "",  # 跨地区，不强制
}
# 纳塔相关（名称可能带引号或长串）
AFFILIATION_TO_REGION["纳茨卡延"] = "纳塔"
AFFILIATION_TO_REGION["米克特兰"] = "纳塔"
AFFILIATION_TO_REGION["特特奥坎"] = "纳塔"
AFFILIATION_TO_REGION["特拉洛坎"] = "纳塔"
AFFILIATION_TO_REGION["维茨特兰"] = "纳塔"
AFFILIATION_TO_REGION["寰宇劫灭"] = "其他"
# 无法归入七国时归为「其他」，避免筛选遗漏
AFFILIATION_TO_REGION["冒险家协会"] = "其他"
AFFILIATION_TO_REGION["南十字船队"] = "璃月"
AFFILIATION_TO_REGION["艾尔卡萨扎莱宫"] = "须弥"
AFFILIATION_TO_REGION["叮铃哐啷蛋卷工坊"] = "枫丹"
AFFILIATION_TO_REGION["红弦"] = "枫丹"


def parse_birthday(birthday_str: str) -> dict:
    """解析生日字符串，如 '3月21日' -> { month: 3, day: 21 }"""
    if not birthday_str or not isinstance(birthday_str, str):
        return {}
    m = re.search(r"(\d{1,2})月(\d{1,2})日", birthday_str)
    if m:
        return {"month": int(m.group(1)), "day": int(m.group(2))}
    return {}


def get_zodiac(month: int, day: int) -> str:
    """根据月日返回星座"""
    for m1, d1, m2, d2, name in ZODIAC_RANGES:
        if (month == m1 and day >= d1) or (month == m2 and day <= d2):
            return name
    return ""


# 七国：用于优先「所属」组织得出的当前所属地（如西风骑士团→蒙德），优于仅「出身地区」的坎瑞亚
REGIONS_SEVEN = {"蒙德", "璃月", "稻妻", "须弥", "枫丹", "纳塔", "至冬"}


def extract_region(stats: dict, other_info: dict) -> str:
    """从所属地区、出身地区、所属等提取主要地区，保证多数角色能划分到地区或「其他」"""
    region_from_table = ""
    # 1) 表格「所属地区」「出身地区」
    for key in ("所属地区", "出身地区"):
        s = (stats.get(key) or "").strip()
        if not s:
            continue
        if s == "其他":
            region_from_table = "其他"
            break
        for region, keywords in REGION_KEYWORDS.items():
            if any(kw in s for kw in keywords):
                region_from_table = region
                break
        if region_from_table:
            break
    # 2) 「所属」组织映射（如西风骑士团→蒙德）
    region_from_aff = ""
    aff = (other_info.get("所属") or "").strip()
    if aff:
        for org, region in AFFILIATION_TO_REGION.items():
            if org in aff and region:
                region_from_aff = region
                break
        if not region_from_aff:
            for region, keywords in REGION_KEYWORDS.items():
                if any(kw in aff for kw in keywords):
                    region_from_aff = region
                    break
    # 3) 若表格只有出身地区=坎瑞亚但所属能得出七国（如凯亚 西风骑士团→蒙德），优先用所属
    if region_from_table == "坎瑞亚" and region_from_aff in REGIONS_SEVEN:
        return region_from_aff
    if region_from_table:
        return region_from_table
    if region_from_aff:
        return region_from_aff
    return "其他"


def to_full_image_url(url: str) -> str:
    """将 wiki 缩略图 URL 转为原图 URL，提升清晰度
    例: .../thumb/a/b/xxx.png/500px-xxx.png -> .../a/b/xxx.png
    """
    if not url or "patchwiki.biligame.com" not in url:
        return url
    if "/thumb/" not in url:
        return url
    # /images/ys/thumb/a/b/xxx.png/500px-xxx.png -> /images/ys/a/b/xxx.png
    url = re.sub(r"/thumb/", "/", url, count=1)
    url = re.sub(r"/\d+px-[^/]+$", "", url)
    return url


def upgrade_image_urls(char: dict) -> None:
    """原地升级角色内所有图片 URL 为原图，并优先用立绘作为主图"""
    # 升级所有图片 URL
    if char.get("image_url"):
        char["image_url"] = to_full_image_url(char["image_url"])
    for obj in [char.get("portraits"), char.get("official_intro")]:
        if isinstance(obj, dict):
            for k, v in list(obj.items()):
                if isinstance(v, str) and v:
                    obj[k] = to_full_image_url(v)
    for arr_key in ("birthday_greetings", "festival_greetings"):
        for item in char.get(arr_key) or []:
            if isinstance(item, dict) and item.get("image_url"):
                item["image_url"] = to_full_image_url(item["image_url"])
    portraits = char.get("portraits") or {}
    preferred = portraits.get("立绘2") or portraits.get("立绘")
    if preferred:
        char["image_url"] = preferred


def build_searchable_text(char: dict) -> str:
    """构建全文检索文本"""
    parts = [
        char.get("name", ""),
        char.get("title", ""),
        char.get("character_id", ""),
        " ".join(char.get("nicknames", [])),
        char.get("official_intro", {}).get("title", ""),
        char.get("official_intro", {}).get("description", "")[:200],
    ]
    stories = char.get("stories", {})
    if isinstance(stories, dict):
        parts.append(" ".join(stories.values())[:500])
    return " ".join(p for p in parts if p).strip()


def enhance_character(char: dict) -> dict:
    """为角色添加增强字段"""
    char = dict(char)
    upgrade_image_urls(char)
    birthday = char.get("birthday", "")
    parsed = parse_birthday(birthday)
    char["birthday_parsed"] = parsed
    if parsed:
        char["zodiac"] = get_zodiac(parsed["month"], parsed["day"])
    else:
        char["zodiac"] = ""

    stats = char.get("stats", {})
    other_info = char.get("other_info", {}) or char.get("stats", {})
    char["region"] = extract_region(stats, other_info)

    # 体型：空时从表格补全；统一「幼女」->「少女」便于筛选
    body = (char.get("body_type") or stats.get("体型") or other_info.get("体型") or "").strip()
    if body == "幼女":
        body = "少女"
    if body:
        char["body_type"] = body

    # 元素：旅行者（岩）等从名称括号内补全
    if not (char.get("element") or "").strip():
        name = (char.get("name") or "").strip()
        if name.startswith("旅行者（") and "）" in name:
            m = re.search(r"旅行者（([^）]+)）", name)
            if m:
                el = m.group(1).strip()
                if el in ("火", "水", "风", "雷", "草", "岩", "冰", "无"):
                    char["element"] = el

    char["searchable_text"] = build_searchable_text(char)
    return char


def export_from_mongodb(uri: str = "mongodb://localhost:27017", db_name: str = "genshin_db") -> list:
    """从 MongoDB 导出角色列表"""
    if not MongoClient:
        raise ImportError("需要安装 pymongo: pip install pymongo")
    client = MongoClient(uri)
    db = client[db_name]
    coll = db["genshin_characters"]
    chars = list(coll.find({}, {"_id": 0}))
    client.close()
    return chars


def main():
    import argparse
    parser = argparse.ArgumentParser(description="从 MongoDB 导出角色并增强字段，或仅对现有 JSON 重新跑增强逻辑")
    parser.add_argument("--reenhance", action="store_true", help="不连 MongoDB，只读 data/characters.json 并重新计算 region/体型等后写回")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    out_dir = root / "data"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "characters.json"

    if getattr(args, "reenhance", False):
        if not out_file.exists():
            print(f"未找到 {out_file}，请先导出或从 MongoDB 导出一次")
            return
        with open(out_file, encoding="utf-8") as f:
            chars = json.load(f)
        enhanced = [enhance_character(c) for c in chars]
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(enhanced, f, ensure_ascii=False, indent=2)
        print(f"已对 {len(enhanced)} 个角色重新计算 region/体型 等并写回 {out_file}")
        return

    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DATABASE", "genshin_db")

    try:
        chars = export_from_mongodb(uri, db_name)
    except Exception as e:
        print(f"MongoDB 连接失败: {e}")
        print("将使用空列表，请先运行爬虫: scrapy crawl genshin_spider")
        chars = []

    enhanced = [enhance_character(c) for c in chars]
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(enhanced, f, ensure_ascii=False, indent=2)

    print(f"已导出 {len(enhanced)} 个角色到 {out_file}")


if __name__ == "__main__":
    main()
