# -*- coding: utf-8 -*-
"""统计 characters.json 中筛选字段取值，便于查漏补缺"""
import json
from pathlib import Path
from collections import defaultdict

p = Path(__file__).resolve().parent.parent / "data" / "characters.json"
chars = json.loads(p.read_text(encoding="utf-8"))

regions = defaultdict(int)
elem = defaultdict(int)
weap = defaultdict(int)
body = defaultdict(int)
stats_region = defaultdict(int)
stats_origin = defaultdict(int)
other_aff = defaultdict(int)
for c in chars:
    regions[c.get("region") or ""] += 1
    elem[c.get("element") or ""] += 1
    weap[c.get("weapon") or ""] += 1
    body[c.get("body_type") or ""] += 1
    st = c.get("stats") or {}
    stats_region[st.get("所属地区") or ""] += 1
    stats_origin[st.get("出身地区") or ""] += 1
    oi = c.get("other_info") or {}
    aff = oi.get("所属") or ""
    other_aff[aff] += 1

out = []
out.append("=== region (导出后) ===")
for k, v in sorted(regions.items(), key=lambda x: -x[1]):
    out.append(f"  {k!r}: {v}")
out.append("\n=== stats 所属地区 ===")
for k, v in sorted(stats_region.items(), key=lambda x: -x[1]):
    out.append(f"  {k!r}: {v}")
out.append("\n=== stats 出身地区 ===")
for k, v in sorted(stats_origin.items(), key=lambda x: -x[1]):
    out.append(f"  {k!r}: {v}")
out.append("\n=== other_info 所属 (前40) ===")
for k, v in sorted(other_aff.items(), key=lambda x: -x[1])[:40]:
    out.append(f"  {k!r}: {v}")
out.append("\n=== element ===")
for k, v in sorted(elem.items(), key=lambda x: -x[1]):
    out.append(f"  {k!r}: {v}")
out.append("\n=== weapon ===")
for k, v in sorted(weap.items(), key=lambda x: -x[1]):
    out.append(f"  {k!r}: {v}")
out.append("\n=== body_type ===")
for k, v in sorted(body.items(), key=lambda x: -x[1]):
    out.append(f"  {k!r}: {v}")

text = "\n".join(out)
print(text)
(Path(__file__).resolve().parent.parent / "data" / "filter_fields_report.txt").write_text(text, encoding="utf-8")
print("\n(已写入 data/filter_fields_report.txt)")
