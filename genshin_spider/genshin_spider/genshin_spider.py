import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.http import Request
from itemloaders import ItemLoader
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import logging
import re
from datetime import datetime

# 自定义Item类
class GenshinCharacterItem(scrapy.Item):
    character_id = scrapy.Field()        # 角色唯一ID
    name = scrapy.Field()                # 角色名称
    rarity = scrapy.Field()              # 星级
    element = scrapy.Field()             # 元素属性
    weapon = scrapy.Field()             # 武器类型
    region = scrapy.Field()             # 所属地区
    description = scrapy.Field()        # 角色描述
    story = scrapy.Field()              # 背景故事
    skills = scrapy.Field()             # 技能列表
    image_urls = scrapy.Field()         # 图片URL
    detail_url = scrapy.Field()         # 详情页URL
    last_updated = scrapy.Field()       # 最后更新时间

# 主爬虫类
class GenshinSpider(scrapy.Spider):
    name = 'genshin_spider'
    allowed_domains = ['wiki.biligame.com']
    start_urls = ['https://wiki.biligame.com/ys/角色']
    
    custom_settings = {
        'DOWNLOAD_DELAY': 1.5,           # 请求延迟防止封禁
        'CONCURRENT_REQUESTS': 4,        # 并发请求数
        'RETRY_TIMES': 3,               # 失败重试次数
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404],
        'ITEM_PIPELINES': {
            'genshin_spider.pipelines.MongoDBPipeline': 300,  # 修改此处
        },
        'LOG_LEVEL': 'INFO'
    }

    def parse(self, response):
        # 解析角色列表页
        character_links = response.css('div.item > a::attr(href)').getall()
        for link in character_links:
            yield Request(
                url=response.urljoin(link),
                callback=self.parse_character,
                errback=self.handle_error
            )
        
        # 处理分页（示例）
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page:
            yield Request(url=response.urljoin(next_page))

    def parse_character(self, response):
        loader = ItemLoader(item=GenshinCharacterItem(), response=response)
        
        # 基础信息提取
        loader.add_value('detail_url', response.url)
        loader.add_css('name', 'h1.page-header__title::text')
        loader.add_css('rarity', 'div.star::attr(class)')  # 通过星星数量判断星级
        loader.add_css('element', 'div.element img::attr(alt)')
        loader.add_css('weapon', 'div.weapon img::attr(alt)')
        loader.add_css('region', 'div.region::text')
        loader.add_css('description', 'div.character-intro::text')
        
        # 背景故事提取
        story_sections = response.css('div.story-section')
        full_story = '\n\n'.join([sec.css('::text').getall() for sec in story_sections])
        loader.add_value('story', full_story)
        
        # 技能信息提取
        skills = []
        for skill in response.css('div.skill-card'):
            skill_data = {
                'name': skill.css('h3.skill-name::text').get(),
                'type': skill.css('div.skill-type::text').get(),
                'description': skill.css('div.skill-desc::text').getall()
            }
            skills.append(skill_data)
        loader.add_value('skills', skills)
        
        # 生成唯一ID
        name = loader.get_collected_values('name')[0]
        element = loader.get_collected_values('element')[0]
        character_id = f"{name}_{element}".lower().replace(' ', '_')
        loader.add_value('character_id', character_id)
        
        # 图片URL
        loader.add_css('image_urls', 'div.character-avatar img::attr(src)')
        
        # 更新时间
        loader.add_value('last_updated', datetime.now().isoformat())
        
        yield loader.load_item()

    def handle_error(self, failure):
        # 错误处理逻辑
        self.logger.error(f"请求失败: {failure.request.url}")
        if failure.check(scrapy.exceptions.TimeoutError):
            self.logger.warn("超时错误，尝试重新调度")
            return failure.request.copy()

# MongoDB存储管道
class MongoDBPipeline:
    collection_name = 'genshin_characters'
    
    def open_spider(self, spider):
        self.client = MongoClient(spider.settings.get('MONGODB_URI', 'mongodb://localhost:27017'))
        self.db = self.client[spider.settings.get('MONGODB_DATABASE', 'genshin_db')]
        self.collection = self.db[self.collection_name]
        # 创建唯一索引
        self.collection.create_index('character_id', unique=True)
    
    def close_spider(self, spider):
        self.client.close()
    
    def process_item(self, item, spider):
        try:
            # 更新或插入数据
            self.collection.update_one(
                {'character_id': item['character_id']},
                {'$set': dict(item)},
                upsert=True
            )
            spider.logger.info(f"更新角色: {item['name']}")
        except DuplicateKeyError:
            spider.logger.warn(f"重复角色: {item['name']}")
        except Exception as e:
            spider.logger.error(f"数据库错误: {str(e)}")
        return item