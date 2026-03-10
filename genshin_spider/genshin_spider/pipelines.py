# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError


class GenshinSpiderPipeline:
    def process_item(self, item, spider):
        return item


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


class CharacterProfileMongoPipeline:
    collection_name = 'genshin_character_profiles'

    def open_spider(self, spider):
        self.client = MongoClient(spider.settings.get('MONGODB_URI', 'mongodb://localhost:27017'))
        self.db = self.client[spider.settings.get('MONGODB_DATABASE', 'genshin_db')]
        self.collection = self.db[self.collection_name]
        self.collection.create_index('name', unique=True)

    def close_spider(self, spider):
        self.client.close()

    def process_item(self, item, spider):
        try:
            self.collection.update_one(
                {'name': item['name']},
                {'$set': dict(item)},
                upsert=True
            )
            spider.logger.info(f"更新角色个人形象: {item['name']}")
        except Exception as e:
            spider.logger.error(f"个人形象存储错误: {str(e)}")
        return item
