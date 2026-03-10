"""
根据 data/characters.json 生成「图片用途清单」：每张图对应哪个角色、哪个字段、用在哪。
输出到 data/image_usage_report.txt（可选 --json 输出 JSON）。
"""
import json
from pathlib import Path


def _collect_paths(obj, prefix: str, out: list[tuple[str, str]]) -> None:
    """递归收集所有 /api/images/xxx 路径，记录 (url, 字段路径)"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            next_prefix = f"{prefix}.{k}" if prefix else k
            if isinstance(v, str) and v.startswith("/api/images/"):
                out.append((v, next_prefix))
            else:
                _collect_paths(v, next_prefix, out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            next_prefix = f"{prefix}[{i}]"
            if isinstance(v, str) and v.startswith("/api/images/"):
                out.append((v, next_prefix))
            else:
                _collect_paths(v, next_prefix, out)


def _path_to_label(path: str) -> str:
    """把 JSON 路径转成可读标签，如 official_intro.portrait_url -> 官方介绍·立绘"""
    label_map = {
        "image_url": "主图/头像",
        "official_intro.portrait_url": "官方介绍·立绘",
        "portraits.立绘": "立绘",
        "portraits.全身": "全身",
    }
    for k, v in label_map.items():
        if path.endswith(k) or path == k:
            return v
    if "birthday_greetings" in path:
        return "生日贺图"
    if "festival_greetings" in path:
        return "节日贺图"
    if "portraits." in path:
        return "立绘/全身等"
    return path


def main():
    import argparse
    parser = argparse.ArgumentParser(description="生成图片用途清单：每张图对应哪个角色、用在哪")
    parser.add_argument("--json", action="store_true", help="输出 JSON 到 data/image_usage_report.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    characters_file = data_dir / "characters.json"

    if not characters_file.exists():
        print(f"未找到 {characters_file}")
        return

    with open(characters_file, encoding="utf-8") as f:
        chars = json.load(f)

    # 按图片路径聚合：(图片路径) -> [(角色名, 字段路径, 可读标签), ...]
    by_image: dict[str, list[tuple[str, str, str]]] = {}

    for c in chars:
        name = c.get("name") or c.get("character_id") or "?"
        collected: list[tuple[str, str]] = []
        _collect_paths(c, "", collected)
        for path_val, field_path in collected:
            if path_val.startswith("/api/images/"):
                label = _path_to_label(field_path)
                by_image.setdefault(path_val, []).append((name, field_path, label))

    # 只取文件名，便于和 data/images/ 里的文件对应
    filename_to_uses: dict[str, list[dict]] = {}
    for full_path, uses in by_image.items():
        filename = full_path.replace("/api/images/", "")
        filename_to_uses[filename] = [
            {"character": name, "field": field, "label": label}
            for name, field, label in uses
        ]

    if args.json:
        out_file = data_dir / "image_usage_report.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(filename_to_uses, f, ensure_ascii=False, indent=2)
        print(f"已写入 {out_file}")
        return

    # 文本报告
    lines = [
        "图片用途清单（由 scripts/image_usage_report.py 生成）",
        "=" * 60,
        "每张图的文件名（data/images/ 下）对应下方「用途」：角色 + 在网站中的用法。",
        "前端用法：image_url=列表/详情头像，official_intro.portrait_url/portraits.立绘=详情立绘，birthday_greetings=生日贺图，festival_greetings=节日贺图。",
        "",
    ]
    for filename in sorted(filename_to_uses.keys()):
        uses = filename_to_uses[filename]
        chars_str = ", ".join(f"{u['character']}（{u['label']}）" for u in uses)
        lines.append(f"  {filename}")
        lines.append(f"    -> {chars_str}")
        lines.append("")
    out_file = data_dir / "image_usage_report.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"已写入 {out_file}，共 {len(filename_to_uses)} 张图片的用途说明。")


if __name__ == "__main__":
    main()
