"""
将 data/characters.json 中 /api/images/xxx.png 与 .jpg 改为 .webp。
用于：已用 optimize_images.py 转成 WebP 后，若 JSON 里仍是 .png/.jpg，可只改 JSON 不重转文件。
"""
import re
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "characters.json"
    if not path.exists():
        print(f"未找到 {path}")
        return
    text = path.read_text(encoding="utf-8")
    new_text = re.sub(r"(/api/images/[a-zA-Z0-9]+)\.(png|jpg|jpeg)", r"\1.webp", text, flags=re.IGNORECASE)
    if new_text == text:
        print("无需修改（未发现 /api/images/xxx.png 或 .jpg）")
        return
    path.write_text(new_text, encoding="utf-8")
    print("已把 characters.json 中的 /api/images/xxx.png 与 .jpg 全部改为 .webp。请重启后端以清除内存缓存。")


if __name__ == "__main__":
    main()
