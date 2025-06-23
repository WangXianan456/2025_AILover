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

        # TODO: 修改为实际的class名
        character_items = response.css('div.item')  # 这里需要你根据实际页面结构修改
        logging.info(f"发现角色卡片数量: {len(character_items)}")

        for item in character_items:
            # 角色名称
            name = item.css('span.itemname::text').get()
            if not name:
                continue
            
            # 角色详情页链接
            detail_url = item.css('a::attr(href)').get()
            if not detail_url:
                continue
            
            # 完整URL
            full_url = urljoin(response.url, detail_url)
            
            # 星级（通过星星图标数量判断）
            stars = len(item.css('div.star div.staricon'))
            
            # 元素属性
            element = item.css('div.element img::attr(alt)').get()
            
            # 武器类型
            weapon = item.css('div.weapon img::attr(alt)').get()
            
            # 图片URL
            image_url = item.css('div.avatar img::attr(src)').get()
            if image_url:
                image_url = urljoin(response.url, image_url)
            
            # 生成角色ID
            character_id = re.search(r'/(\w+)\.png', image_url).group(1) if image_url else name.lower().replace(' ', '_')
            
            meta = {
                'character_id': character_id,
                'name': name.strip(),
                'rarity': stars,
                'element': element,
                'weapon': weapon,
                'image_url': image_url
            }
            
            # 请求详情页
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
                    key = columns[0].css('::text').get().strip()
                    value = columns[1].css('::text').get().strip()
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
            'character_id': meta['character_id'],
            'name': meta['name'],
            'rarity': meta['rarity'],
            'element': meta['element'],
            'weapon': meta['weapon'],
            'image_url': meta['image_url'],
            'detail_url': response.url,
            'story': story,
            'stats': stats,
            'skills': skills,
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