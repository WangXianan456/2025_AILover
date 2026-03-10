"""
将 characters.json 中引用的远程图片下载到 data/images/，并把 JSON 中的 URL 替换为本地路径 /api/images/<filename>。
运行前请先执行 scripts/export_characters.py 生成 data/characters.json。
依赖：pip install httpx
"""
import hashlib
import json
from pathlib import Path

import httpx

# 只下载这些域名的图片（与后端 image-proxy 白名单一致）
ALLOWED_HOSTS = (
    "patchwiki.biligame.com",
    "i0.hdslb.com",
    "i1.hdslb.com",
    "i2.hdslb.com",
)
USER_AGENT = "Mozilla/5.0 (compatible; AIlover/1.0)"


def url_allowed(url: str) -> bool:
    if not url or not url.startswith("http"):
        return False
    try:
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        return any(h in host for h in ALLOWED_HOSTS)
    except Exception:
        return False


def is_local_path(url: str) -> bool:
    return isinstance(url, str) and (url.startswith("/api/images/") or url.startswith("/images/"))


def get_ext_from_content_type(ct: str) -> str:
    if "jpeg" in ct or "jpg" in ct:
        return ".jpg"
    if "png" in ct:
        return ".png"
    if "gif" in ct:
        return ".gif"
    if "webp" in ct:
        return ".webp"
    return ".png"


def get_ext_from_url(url: str) -> str:
    path = url.split("?")[0]
    if path.endswith(".png"):
        return ".png"
    if path.endswith(".jpg") or path.endswith(".jpeg"):
        return ".jpg"
    if path.endswith(".gif"):
        return ".gif"
    if path.endswith(".webp"):
        return ".webp"
    return ".png"


def filename_for_url(url: str, content_type: str = "") -> str:
    h = hashlib.sha256(url.encode()).hexdigest()[:16]
    ext = get_ext_from_content_type(content_type) or get_ext_from_url(url)
    return f"{h}{ext}"


def collect_urls(obj, out: set) -> None:
    """递归收集所有字符串 URL（仅 http 且允许的域名）"""
    if isinstance(obj, dict):
        for v in obj.values():
            collect_urls(v, out)
    elif isinstance(obj, list):
        for v in obj:
            collect_urls(v, out)
    elif isinstance(obj, str) and obj.startswith("http") and url_allowed(obj):
        out.add(obj)


def replace_urls_in_place(obj, mapping: dict) -> None:
    """原地把 mapping 中的 key 替换为 value"""
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if isinstance(v, str) and v in mapping:
                obj[k] = mapping[v]
            else:
                replace_urls_in_place(v, mapping)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str) and v in mapping:
                obj[i] = mapping[v]
            else:
                replace_urls_in_place(v, mapping)


def main():
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    characters_file = data_dir / "characters.json"
    images_dir = data_dir / "images"

    if not characters_file.exists():
        print(f"未找到 {characters_file}，请先运行 scripts/export_characters.py")
        return

    images_dir.mkdir(parents=True, exist_ok=True)

    with open(characters_file, encoding="utf-8") as f:
        chars = json.load(f)

    urls = set()
    for c in chars:
        collect_urls(c, urls)

    # 排除已是本地路径的
    to_download = [u for u in urls if not is_local_path(u)]
    if not to_download:
        print("没有需要下载的远程图片（可能已全部本地化）")
        return

    print(f"共 {len(to_download)} 个远程图片待下载到 {images_dir}")

    url_to_local = {}
    with httpx.Client(follow_redirects=True, timeout=30.0, headers={"User-Agent": USER_AGENT}) as client:
        for i, url in enumerate(to_download, 1):
            try:
                r = client.get(url)
                r.raise_for_status()
                ct = r.headers.get("content-type", "") or ""
                name = filename_for_url(url, ct)
                path = images_dir / name
                path.write_bytes(r.content)
                local_path = f"/api/images/{name}"
                url_to_local[url] = local_path
                if i % 20 == 0 or i == len(to_download):
                    print(f"  已下载 {i}/{len(to_download)}")
            except Exception as e:
                print(f"  跳过 {url[:60]}... : {e}")

    if not url_to_local:
        print("没有成功下载任何图片")
        return

    replace_urls_in_place(chars, url_to_local)
    with open(characters_file, "w", encoding="utf-8") as f:
        json.dump(chars, f, ensure_ascii=False, indent=2)

    print(f"已替换 {len(url_to_local)} 处 URL 为本地路径，并写回 {characters_file}")


if __name__ == "__main__":
    main()
