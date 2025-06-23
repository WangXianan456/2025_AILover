import scrapy
from scrapy import Request
from urllib.parse import urljoin
import logging
import re
from datetime import datetime

class GenshinSpider(scrapy.Spider):
    name = 'genshin_spider'
    allowed_domains = ['wiki.biligame.com']
    start_urls = ['https://wiki.biligame.com/ys/角色']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 1.5,
        'CONCURRENT_REQUESTS': 3,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'RETRY_TIMES': 3,
        'LOG_LEVEL': 'DEBUG'
    }

    def parse(self, response):
        logging.info(f"开始解析角色列表页: {response.url}")

        # 保存页面内容到本地，便于分析
        with open("page_debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)

        # 角色卡片选择器修正
        character_items = response.css('div.divsort.g')
        logging.info(f"发现角色卡片数量: {len(character_items)}")

        for item in character_items:
            # 名称
            name = item.css('div.L::text').get()
            if not name:
                name = item.css('a:last-child::text').get()
            if not name:
                continue

            # 详情页链接
            detail_url = item.css('a:last-child::attr(href)').get()
            if not detail_url:
                continue
            full_url = urljoin(response.url, detail_url)

            # 星级
            class_str = ' '.join(item.attrib.get('class', '').split())
            rarity = 5 if 'C5星' in class_str else 4 if 'C4星' in class_str else None

            # 元素属性和武器类型
            element = item.attrib.get('data-param2', '').strip()
            weapon = item.attrib.get('data-param3', '').strip()

            # 图片URL
            image_url = item.css('img::attr(src)').get()
            if image_url:
                image_url = urljoin(response.url, image_url)

            # 生成角色ID
            character_id = re.sub(r'\W+', '', name.strip().lower())

            meta = {
                'character_id': character_id,
                'name': name.strip(),
                'rarity': rarity,
                'element': element,
                'weapon': weapon,
                'image_url': image_url
            }

            yield Request(
                url=full_url,
                callback=self.parse_character,
                meta=meta,
                errback=self.handle_error
            )

    def parse_character(self, response):
        meta = response.meta
        logging.info(f"解析角色详情页: {meta['name']} - {response.url}")
        
        # 背景故事
        story = " ".join(response.css('div.story-section ::text').getall()).strip()
        
        # 角色属性表格
        stats = {}
        stat_table = response.css('table.wikitable')
        if stat_table:
            for row in stat_table.css('tr')[1:]:
                columns = row.css('td')
                if len(columns) >= 2:
                    key = (columns[0].css('::text').get() or '').strip()
                    value = (columns[1].css('::text').get() or '').strip()
                    stats[key] = value
        
        # 角色技能
        skills = []
        skill_tabs = response.css('div.tabbertab')
        for tab in skill_tabs:
            skill_name = tab.css('h3::text').get()
            skill_desc = " ".join(tab.css('div.wiki-paragraph ::text').getall()).strip()
            if skill_name and skill_desc:
                skills.append({
                    'name': skill_name,
                    'description': skill_desc
                })
        
        # 构建完整角色数据
        character_data = {
            'character_id': str(meta['character_id']),
            'name': str(meta['name']),
            'rarity': int(meta['rarity']) if meta['rarity'] else None,
            'element': str(meta['element']),
            'weapon': str(meta['weapon']),
            'image_url': str(meta['image_url']) if meta['image_url'] else '',
            'detail_url': str(response.url),
            'story': str(story),
            'stats': {str(k): str(v) for k, v in stats.items()},
            'skills': [{'name': str(s['name']), 'description': str(s['description'])} for s in skills],
            'last_updated': datetime.now().isoformat()
        }
        
        yield character_data

    def handle_error(self, failure):
        request = failure.request
        logging.error(f"请求失败: {request.url}")
        logging.error(f"错误原因: {failure.value}")
        
        # 对于详情页失败，至少返回基本信息
        if 'meta' in request.meta:
            base_data = request.meta.copy()
            base_data['error'] = str(failure.value)
            yield base_data