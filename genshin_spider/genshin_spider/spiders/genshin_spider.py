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

    def _parse_portraits(self, response):
        """提取立绘：立绘、介绍立绘、抽卡立绘、入队动作、站立动作等"""
        portraits = {}
        # h2#立绘 后的 main-line-wrap > resp-tabs
        tabs = response.xpath(
            '//h2[span[@id="立绘"]]/following-sibling::div[1]//ul[contains(@class,"resp-tabs-list")]/li/span[@class="tab-panel"]/text()'
        ).getall()
        contents = response.xpath(
            '//h2[span[@id="立绘"]]/following-sibling::div[1]//div[contains(@class,"resp-tab-content")]'
        )
        for i, content in enumerate(contents):
            if i >= len(tabs):
                break
            label = tabs[i].strip()
            img = content.css('a.image img::attr(src)').get()
            if img and not img.startswith('http'):
                img = urljoin(response.url, img)
            if img:
                portraits[label] = img
        return portraits

    def _parse_official_intro(self, response):
        """提取官方介绍：壹·人物（立绘图+标题+描述）+ 贰·故事"""
        result = {'portrait_url': '', 'title': '', 'description': '', 'story_er': ''}
        # 壹·人物 下的 thumb（含官方介绍图）
        thumb = response.xpath(
            '//h4[contains(., "壹·人物")]/following-sibling::div[contains(@class,"thumb")][1]'
        )
        if thumb:
            img = thumb.css('a.image img::attr(src)').get()
            if img:
                result['portrait_url'] = urljoin(response.url, img) if not img.startswith('http') else img
        # 壹·人物 下的 p 文本（标题 + 描述）
        intro_p = response.xpath(
            '//h4[contains(., "壹·人物")]/following-sibling::p[1]'
        )
        if intro_p:
            text = intro_p.xpath('string(.)').get()
            if text:
                text = text.strip()
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                for line in lines:
                    if '=' not in line and len(line) < 50:
                        result['title'] = line
                        break
                result['description'] = re.sub(r'=+\s*', '', text).strip()
        # 贰·故事：h4 后的 div.row 或 p
        story_section = response.xpath(
            '//h4[contains(., "贰·故事")]/following-sibling::div[contains(@class,"row")][1]'
        )
        if story_section:
            result['story_er'] = (story_section.xpath('string(.)').get() or '').strip()
        else:
            story_p = response.xpath(
                '//h4[contains(., "贰·故事")]/following-sibling::p[1]'
            )
            if story_p:
                result['story_er'] = (story_p.xpath('string(.)').get() or '').strip()
        return result

    def _parse_other_info(self, response):
        """解析其它信息表：生日、昵称、体型、CV 等（h2#其它信息 或 #其他信息）"""
        result = {
            'birthday': '',
            'nicknames': [],
            'body_type': '',
            'voice_actors': {'cn': '', 'jp': '', 'kr': '', 'en': ''},
            'affiliation': '',
            'occupation': '',
            'raw': {}
        }
        # 兼容 其它信息 / 其他信息 两种 id
        table = response.xpath(
            '//h2[span[@id="其它信息"] or span[@id="其他信息"]]/following-sibling::div[1]//table[contains(@class,"wikitable")]//tr'
        )
        for row in table:
            th = row.xpath('.//th//text()').get()
            td = row.xpath('.//td')
            if not th or not td:
                continue
            th = th.strip()
            text = td.xpath('string(.)').get()
            text = (text or '').strip()
            result['raw'][th] = text
            if th in ('昵称/外号', '昵称', '外号'):
                result['nicknames'] = [n.strip() for n in re.split(r'[、，,]', text) if n.strip()]
            elif th == '生日':
                result['birthday'] = text
            elif th == '体型':
                result['body_type'] = text
            elif th == '中文CV':
                result['voice_actors']['cn'] = text
            elif th == '日文CV':
                result['voice_actors']['jp'] = text
            elif th == '韩文CV':
                result['voice_actors']['kr'] = text
            elif th == '英文CV':
                result['voice_actors']['en'] = text
            elif th == '所属':
                result['affiliation'] = text
            elif th == '职业':
                result['occupation'] = text
        return result

    def _parse_constellations(self, response):
        """解析命之座：名称 + 效果"""
        constellations = []
        rows = response.xpath(
            '//h2[span[@id="命之座"]]/following-sibling::div[1]//table[contains(@class,"wikitable")]//tr[td]'
        )
        for row in rows:
            name_td = row.xpath('.//td[1]')
            effect_td = row.xpath('.//td[2]')
            if not name_td or not effect_td:
                continue
            name = name_td.xpath('string(.)').get()
            effect = effect_td.xpath('string(.)').get()
            if name and name.strip():
                constellations.append({
                    'name': name.strip(),
                    'effect': (effect or '').strip()
                })
        return constellations

    def _parse_festival_greetings(self, response):
        """提取节日贺图：情人节、中秋节等（结构同生日贺图，tab 非纯年份）"""
        greetings = []
        section = response.xpath(
            '//p[contains(., "节日贺图")]/following-sibling::div[contains(@class,"poke-bg")][1]'
        )
        if not section:
            return greetings
        tabs = section.xpath('.//ul[contains(@class,"resp-tabs-list")]/li/span[@class="tab-panel"]/text()').getall()
        contents = section.xpath('.//div[contains(@class,"resp-tab-content")]')
        for i, content in enumerate(contents):
            if i >= len(tabs):
                break
            label = tabs[i].strip()
            if re.match(r'^\d{4}$', label):
                continue
            text = content.xpath('.//p[string-length(normalize-space())>0]').xpath('string(.)').get()
            img = content.css('a.image img::attr(src)').get()
            if img and not img.startswith('http'):
                img = urljoin(response.url, img)
            greetings.append({'label': label, 'text': (text or '').strip(), 'image_url': img or ''})
        return greetings

    def _parse_birthday_greetings(self, response):
        """提取生日贺图：按年份存储 {year: {text, image_url}}，部分角色可能无此内容"""
        greetings = []
        # 找到「生日贺图」后的 poke-bg，其 tab 为年份（2023、2024 等）
        bday_section = response.xpath(
            '//p[contains(., "生日贺图")]/following-sibling::div[contains(@class,"poke-bg")][1]'
        )
        if not bday_section:
            return greetings
        tabs = bday_section.xpath('.//ul[contains(@class,"resp-tabs-list")]/li/span[@class="tab-panel"]/text()').getall()
        contents = bday_section.xpath('.//div[contains(@class,"resp-tab-content")]')
        for i, content in enumerate(contents):
            if i >= len(tabs):
                break
            year = tabs[i].strip()
            if not re.match(r'^\d{4}$', year):
                continue
            text = content.xpath('.//p[string-length(normalize-space())>0]').xpath('string(.)').get()
            img = content.css('a.image img::attr(src)').get()
            if img and not img.startswith('http'):
                img = urljoin(response.url, img)
            greetings.append({'year': year, 'text': (text or '').strip(), 'image_url': img or ''})
        return greetings

    def _parse_stories(self, response):
        """从角色故事表格中提取所有故事段落（角色详细、角色故事1~5、狼的还乡曲、神之眼等）
        表格结构：tr(th 标题) + tr(td 内容) 交替出现
        """
        stories = {}
        # 找到角色故事区域的表格（h2#角色故事 后的第一个 div 内的 wikitable）
        story_rows = response.xpath(
            '//h2[span[@id="角色故事"]]/following-sibling::div[1]//table[contains(@class,"wikitable")]//tr'
        )
        current_title = None
        for row in story_rows:
            th = row.xpath('.//th//text()').get()
            td = row.xpath('.//td')
            if th:
                # 提取标题，去掉括号中的解锁条件，如「角色故事1 （解锁条件：好感2级）」->「角色故事1」
                current_title = th.strip().split('（')[0].strip()
            if td and current_title:
                text = td.xpath('string(.)').get()
                if text and text.strip():
                    stories[current_title] = text.strip()
        # 若无分段落，尝试旧版单段提取（兼容部分页面结构）
        if not stories:
            single = response.xpath(
                '//h2[span[@id="角色故事"]]/following-sibling::div[1]//table[contains(@class,"wikitable")]//td'
            ).xpath('string(.)').get()
            if single and single.strip():
                stories['角色详细'] = single.strip()
        return stories

    def parse_character(self, response):
        meta = response.meta
        logging.info(f"解析角色详情页: {meta['name']} - {response.url}")

        # 1. 图片
        image_url = response.css('meta[itemprop="image"]::attr(content)').get()
        if not image_url:
            # 备用方案：立绘图片
            image_url = response.css('.main-line-wrap img::attr(src)').get()
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(response.url, image_url)

        # 2. 角色基础信息表格（仅取第一个 wikitable，即页顶「称号/所属地区/出身地区」等主表）
        # 单元格内常有链接/图片，用 td 内全部文本（含子节点）才能正确拿到「所属地区」「出身地区」等
        from scrapy.selector import Selector
        first_table_html = response.css('table.wikitable').get()
        if not first_table_html:
            info_rows = []
        else:
            info_rows = Selector(text=first_table_html).css('tr')
        info_dict = {}
        for row in info_rows:
            th = row.css('th::text').get()
            td_parts = row.css('td ::text').getall()
            td = ' '.join(p.strip() for p in td_parts if p and p.strip()).strip() if td_parts else ''
            if th and td:
                info_dict[th.strip()] = td

        # 3. 元素、武器类型
        element = info_dict.get('神之眼', '') or info_dict.get('元素', '')
        weapon = info_dict.get('武器类型', '') or info_dict.get('武器', '')

        # 4. 稀有度
        rarity = None
        rarity_td = None
        for row in info_rows:
            th = row.css('th::text').get()
            if th and '稀有度' in th:
                rarity_td = row.css('td img::attr(alt)').get()
                break
        if rarity_td:
            if '5星' in rarity_td:
                rarity = 5
            elif '4星' in rarity_td:
                rarity = 4

        # 5. 角色故事（完整提取：角色详细、角色故事1~5、狼的还乡曲、神之眼等）
        stories = self._parse_stories(response)
        # 兼容旧字段：合并所有故事为 story，供简要展示
        story = '\n\n'.join(f'【{k}】\n{v}' for k, v in stories.items()) if stories else ''

        # 6. 立绘（立绘、介绍立绘、抽卡立绘、入队动作、站立动作等）
        portraits = self._parse_portraits(response)

        # 7. 官方介绍（壹·人物：立绘图 + 标题 + 详细介绍）
        official_intro = self._parse_official_intro(response)

        # 8. 生日贺图（按年份：text + image_url，部分角色可能无）
        birthday_greetings = self._parse_birthday_greetings(response)

        # 9. 节日贺图（情人节、中秋节等，部分角色可能无）
        festival_greetings = self._parse_festival_greetings(response)

        # 10. 其它信息（生日、昵称、体型、CV 等）
        other_info = self._parse_other_info(response)

        # 11. 命之座
        constellations = self._parse_constellations(response)

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
        
        # 称号（首表）
        title = info_dict.get('称号', '')

        # 构建完整角色数据        
        character_data = {
            'character_id': str(meta['character_id']),
            'name': str(meta['name']),
            'title': title,
            'rarity': rarity,
            'element': element,
            'weapon': weapon,
            'image_url': image_url or str(meta.get('image_url', '')),
            'detail_url': str(response.url),
            'story': story,
            'stories': stories,
            'portraits': portraits,
            'official_intro': official_intro,
            'birthday_greetings': birthday_greetings,
            'festival_greetings': festival_greetings,
            'birthday': other_info['birthday'],
            'nicknames': other_info['nicknames'],
            'body_type': other_info['body_type'],
            'voice_actors': other_info['voice_actors'],
            'affiliation': other_info['affiliation'],
            'occupation': other_info['occupation'],
            'other_info': other_info['raw'],
            'constellations': constellations,
            'stats': {str(k): str(v) for k, v in info_dict.items()},
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