"""
将 data/images/ 中的 PNG/JPEG/GIF 转为 WebP，在几乎不损失观感的前提下显著减小体积，
并更新 data/characters.json 中的图片路径。
依赖：pip install Pillow
"""
import json
import warnings
from pathlib import Path

# 部分图片 EXIF 损坏，仅影响元数据，不影响转 WebP，忽略警告
warnings.filterwarnings("ignore", message=".*EXIF.*", module="PIL.*")

try:
    from PIL import Image
except ImportError:
    Image = None

# 高画质 WebP：quality 90–95 肉眼几乎无差异，体积通常可降 30%–50%
WEBP_QUALITY = 92
# method 0–6，越大压缩越好、越慢
WEBP_METHOD = 6

SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".gif"}


def _collect_to_convert(images_dir: Path) -> list[Path]:
    """收集需要转换的文件列表"""
    out = []
    for f in images_dir.iterdir():
        if not f.is_file():
            continue
        if f.suffix.lower() == ".webp":
            continue
        if f.suffix.lower() not in SUPPORTED_EXT:
            continue
        if f.with_suffix(".webp").exists():
            continue
        out.append(f)
    return out


def optimize_images(images_dir: Path, dry_run: bool = False, to_convert: list[Path] | None = None) -> dict[str, str]:
    """
    将 images_dir 下非 WebP 图片转为 WebP，返回 原路径 -> 新路径 的映射（用于更新 JSON）。
    """
    if not Image:
        raise ImportError("需要安装 Pillow: pip install Pillow")

    if to_convert is None:
        to_convert = _collect_to_convert(images_dir)
    total = len(to_convert)
    mapping = {}

    for i, f in enumerate(to_convert, 1):
        # 每 10 张或最后一张打印进度
        if total < 10 or i % 10 == 0 or i == total:
            print(f"  [ {i}/{total} ] {f.name}")
        out = f.with_suffix(".webp")
        try:
            img = Image.open(f)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGBA")
            else:
                img = img.convert("RGB")

            if not dry_run:
                img.save(out, "WEBP", quality=WEBP_QUALITY, method=WEBP_METHOD)
                f.unlink()
            mapping[f.name] = out.name
        except Exception as e:
            print(f"  跳过 {f.name}: {e}")
    return mapping


def update_characters_json(characters_file: Path, mapping: dict[str, str], dry_run: bool = False) -> int:
    """把 JSON 中 /api/images/old 替换为 /api/images/new，返回替换次数"""
    if not mapping or not characters_file.exists():
        return 0

    with open(characters_file, encoding="utf-8") as f:
        data = json.load(f)

    total = [0]
    for old_name, new_name in mapping.items():
        old_path = f"/api/images/{old_name}"
        new_path = f"/api/images/{new_name}"
        _replace_in_place(data, old_path, new_path, total)
    count = total[0]

    if count and not dry_run:
        with open(characters_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    return count


def _replace_in_place(obj, old: str, new: str, counter: list) -> None:
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str) and v == old:
                obj[k] = new
                counter[0] += 1
            else:
                _replace_in_place(v, old, new, counter)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str) and v == old:
                obj[i] = new
                counter[0] += 1
            else:
                _replace_in_place(v, old, new, counter)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="将 data/images 转为 WebP 并更新 characters.json")
    parser.add_argument("--dry-run", action="store_true", help="只统计不写入")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    images_dir = data_dir / "images"
    characters_file = data_dir / "characters.json"

    if not images_dir.exists():
        print("未找到 data/images/，请先运行 scripts/download_images.py")
        return

    to_convert = _collect_to_convert(images_dir)
    if not to_convert:
        print("没有需要转换的图片（已是 WebP 或无可处理格式）")
        return

    print(f"正在处理 {images_dir}（转为 WebP，quality={WEBP_QUALITY}）共 {len(to_convert)} 张...")
    mapping = optimize_images(images_dir, dry_run=args.dry_run, to_convert=to_convert)

    print(f"已转换 {len(mapping)} 个文件" + ("（dry-run，未写入）" if args.dry_run else ""))

    count = update_characters_json(characters_file, mapping, dry_run=args.dry_run)
    if count:
        print(f"已在 characters.json 中更新 {count} 处图片路径" + ("（dry-run，未写入）" if args.dry_run else ""))
    else:
        print("characters.json 中无需更新或文件不存在")


if __name__ == "__main__":
    main()
