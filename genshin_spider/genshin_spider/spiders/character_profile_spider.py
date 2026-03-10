import scrapy
from pymongo import MongoClient
from urllib.parse import quote
from datetime import datetime
import re

class CharacterProfileSpider(scrapy.Spider):
    name = "character_profile_spider"
    allowed_domains = ["wiki.biligame.com"]

    custom_settings = {
        'DOWNLOAD_DELAY': 1.0,
        'CONCURRENT_REQUESTS': 2,
        'ITEM_PIPELINES': {
            'genshin_spider.pipelines.CharacterProfileMongoPipeline': 300,
        },
        'LOG_LEVEL': 'INFO'
    }

    def start_requests(self):
        # 连接MongoDB，获取所有角色名字
        client = MongoClient(self.settings.get('MONGODB_URI', 'mongodb://localhost:27017'))
        db = client[self.settings.get('MONGODB_DATABASE', 'genshin_db')]
        chars = db['genshin_characters'].find({}, {'name': 1})
        for char in chars:
            name = char['name']
            url = f"https://wiki.biligame.com/ys/{quote(name)}"
            yield scrapy.Request(url, callback=self.parse_profile, meta={'name': name})
        client.close()

    def parse_profile(self, response):
        name = response.meta['name']
        info_box = response.css('table.infobox, table')

        # 遍历表格行，构建键值对
        info_dict = {}
        for tr in info_box.css('tr'):
            key = tr.css('th::text, td b::text, td strong::text').get()
            value = tr.css('td::text').get()
            if key and value:
                info_dict[key.strip()] = value.strip()

        # 简介
        description = info_dict.get('角色介绍') or response.css('p::text').get()

        # 昵称/别称
        nicknames = []
        alias = info_dict.get('别称') or info_dict.get('外号')
        if alias:
            nicknames = [n.strip() for n in re.split('[、，,]', alias) if n.strip()]

        # 故事（多条）
        story = []
        for sec in response.css('div.story-section, div.character-story, div.story'):
            text = ''.join(sec.css('::text').getall()).strip()
            if text:
                story.append(text)

        # 图片
        images = []
        for img in response.css('img'):
            src = img.attrib.get('src', '')
            if src and src.startswith('http') and src not in images:
                images.append(src)
            elif src and src.startswith('/'):
                full_url = response.urljoin(src)
                if full_url not in images:
                    images.append(full_url)

        profile = {
            'name': name,
            'url': response.url,
            'title': response.css('h1.firstHeading::text').get(),
            'rarity': info_dict.get('稀有度'),
            'element': info_dict.get('神之眼'),
            'weapon': info_dict.get('武器'),
            'birthday': info_dict.get('生日'),
            'affiliation': info_dict.get('所属'),
            'description': description,
            'nicknames': nicknames,
            'story': story,
            'images': images,
            'last_updated': datetime.now().isoformat()
        }
        yield profile
