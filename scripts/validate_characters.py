# -*- coding: utf-8 -*-
"""
检查 data/characters.json 中筛选字段是否完整，便于不重复、不遗漏。
输出：缺失 region / element / weapon / body_type 的角色列表，以及重复 character_id 告警。
"""
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "characters.json"
    if not path.exists():
        print(f"未找到 {path}")
        return
    chars = json.loads(path.read_text(encoding="utf-8"))

    ids = []
    missing_region = []
    missing_element = []
    missing_weapon = []
    missing_body = []
    missing_rarity = []

    for c in chars:
        name = c.get("name") or c.get("character_id") or "?"
        cid = c.get("character_id")
        if cid:
            ids.append(cid)
        if not (c.get("region") or "").strip():
            missing_region.append(name)
        if not (c.get("element") or "").strip():
            missing_element.append(name)
        if not (c.get("weapon") or "").strip():
            missing_weapon.append(name)
        if not (c.get("body_type") or "").strip():
            missing_body.append(name)
        if c.get("rarity") is None:
            missing_rarity.append(name)

    dup = [x for x in set(ids) if ids.count(x) > 1]
    lines = [
        f"总角色数: {len(chars)}",
        f"重复 character_id: {dup if dup else '无'}",
        "",
        f"缺失 region: {len(missing_region)} 人",
        "  " + ", ".join(missing_region[:30]) + (" ..." if len(missing_region) > 30 else ""),
        "",
        f"缺失 element: {len(missing_element)} 人",
        "  " + ", ".join(missing_element[:30]) + (" ..." if len(missing_element) > 30 else ""),
        "",
        f"缺失 weapon: {len(missing_weapon)} 人",
        "  " + ", ".join(missing_weapon[:30]) + (" ..." if len(missing_weapon) > 30 else ""),
        "",
        f"缺失 body_type: {len(missing_body)} 人",
        "  " + ", ".join(missing_body[:30]) + (" ..." if len(missing_body) > 30 else ""),
        "",
        f"缺失 rarity: {len(missing_rarity)} 人",
        "  " + ", ".join(missing_rarity[:30]) + (" ..." if len(missing_rarity) > 30 else ""),
    ]
    text = "\n".join(lines)
    print(text)
    out = root / "data" / "validate_characters_report.txt"
    out.write_text(text, encoding="utf-8")
    print(f"\n已写入 {out}")

if __name__ == "__main__":
    main()
