import scrapy

class CharacterDetailDownloader(scrapy.Spider):
    name = "character_detail_downloader"
    allowed_domains = ["wiki.biligame.com"]
    start_urls = [
        "https://wiki.biligame.com/ys/%E8%89%BE%E5%B0%94%E6%B5%B7%E6%A3%AE"
    ]

    custom_settings = {
        'LOG_LEVEL': 'INFO'
    }

    def parse(self, response):
        # 保存页面内容到本地
        with open("character_detail_艾尔海森.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        self.logger.info("已保存角色详情页 HTML 到 character_detail_艾尔海森.html")
