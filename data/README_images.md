# 本地图片与用途说明

## 图片从哪来、代表什么、用在哪？

- **来源**：`scripts/download_images.py` 从资料站（wiki/图床）按 `data/characters.json` 里的 URL 下载图片，保存到 `data/images/`，文件名是「URL 的 hash」（如 `7a99e377e7ff4342.png`），用于去重和唯一标识。
- **含义与位置**：**每张图对应谁、用在什么场合，都记录在 `data/characters.json` 里**，不是写在文件名上。下载脚本会把 JSON 里原来的远程 URL 全部替换成 `/api/images/文件名`，所以：
  - 同一个文件可能被多个角色、多个字段引用（例如同一张立绘既做头像又做详情主图）；
  - 要查「这张图是谁的、用在哪」，看 JSON 里出现该路径的**角色 + 字段**即可。

## 字段与网站上的用法

| JSON 字段 | 在网站中的用法 |
|-----------|----------------|
| `image_url` | 角色列表头像、详情页主图（若没有立绘则用此图） |
| `official_intro.portrait_url` | 官方介绍用的立绘 |
| `portraits.立绘` / `portraits.全身` | 立绘、全身图（详情页优先用立绘） |
| `birthday_greetings[].image_url` | 生日贺图 |
| `festival_greetings[].image_url` | 节日贺图 |

前端会根据上述字段取图并显示在对应位置，无需再手动「放到某处」——只要 `characters.json` 里该角色、该字段指向 `/api/images/xxx`，页面上就会在对应位置显示这张图。

## 如何查「某张图代表什么、用在哪」

在项目根目录、已激活 `.venv` 下执行：

```bash
python scripts/image_usage_report.py
```

会在 `data/image_usage_report.txt` 生成清单：按文件名列出每张图被哪些角色、哪些用途引用。例如：

```
  7a99e377e7ff4342.png
    -> 丝柯克（主图/头像）
```

需要机器可读的映射时，可加 `--json` 输出到 `data/image_usage_report.json`。
