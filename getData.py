import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin

def scrape_genshin_characters():
    base_url = "https://wiki.biligame.com/ys/角色"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": base_url
    }
    
    try:
        # 发送HTTP请求
        response = requests.get(base_url, headers=headers)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return []
        
        # 解析HTML内容
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 定位角色容器 - 使用CSS选择器
        character_container = soup.select_one('div.resp-tab-content')
        
        if not character_container:
            print("未找到角色容器")
            return []
        
        # 提取所有角色卡片
        character_items = character_container.select('div.item')
        
        characters = []
        
        # 解析每个角色卡片
        for item in character_items:
            # 角色名称
            name_elem = item.select_one('span.itemname')
            name = name_elem.text.strip() if name_elem else "未知"
            
            # 角色星级 (通过星星数量判断)
            star_div = item.select_one('div.star')
            rarity = len(star_div.select('div.staricon')) if star_div else 0
            
            # 元素属性
            element_elem = item.select_one('div.element img')
            element = element_elem.get('alt') if element_elem and element_elem.has_attr('alt') else "未知"
            
            # 武器类型
            weapon_elem = item.select_one('div.weapon img')
            weapon = weapon_elem.get('alt') if weapon_elem and weapon_elem.has_attr('alt') else "未知"
            
            # 角色详情页链接
            link_elem = item.select_one('a')
            detail_url = urljoin(base_url, link_elem.get('href')) if link_elem else ""
            
            # 角色图片
            img_elem = item.select_one('div.avatar img')
            img_url = urljoin(base_url, img_elem.get('src')) if img_elem else ""
            
            # 提取角色ID（从图片URL中提取）
            character_id = re.search(r'/(\w+)\.png', img_url).group(1) if img_url else ""
            
            characters.append({
                "id": character_id,
                "name": name,
                "rarity": rarity,
                "element": element,
                "weapon": weapon,
                "detail_url": detail_url,
                "image_url": img_url
            })
        
        return characters
    
    except Exception as e:
        print(f"爬取过程中发生错误: {str(e)}")
        return []
    
def scrape_character_details(detail_url, headers):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": detail_url
    }
    try:
        response = requests.get(detail_url, headers=headers)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"详情页请求失败: {detail_url}")
            return {}
        
        detail_soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取详细信息
        details = {}
        
        # 1. 角色背景故事
        story_section = detail_soup.select_one('div#角色故事')
        if story_section:
            story_text = ""
            for p in story_section.select('div.wiki-paragraph'):
                story_text += p.text.strip() + "\n\n"
            details["story"] = story_text
        
        # 2. 角色属性表格
        stats_table = detail_soup.select_one('table.wikitable')
        if stats_table:
            stats = {}
            for row in stats_table.select('tr')[1:]:  # 跳过标题行
                cells = row.select('td')
                if len(cells) >= 2:
                    key = cells[0].text.strip()
                    value = cells[1].text.strip()
                    stats[key] = value
            details["stats"] = stats
        
        # 3. 角色技能
        skills = []
        skill_sections = detail_soup.select('div.tabbertab')
        for section in skill_sections:
            skill_name = section.select_one('h3').text.strip()
            skill_desc = section.select_one('div.wiki-paragraph').text.strip()
            skills.append({"name": skill_name, "description": skill_desc})
        details["skills"] = skills
        
        return details
    
    except Exception as e:
        print(f"详情页爬取出错: {str(e)}")
        return {}
    
if __name__ == "__main__":
    # 执行爬取
    characters = scrape_genshin_characters()
    
    # 打印结果
    print(f"成功爬取 {len(characters)} 个角色信息")
    
    # 保存为JSON文件
    with open('genshin_characters.json', 'w', encoding='utf-8') as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)
    
    # 保存为CSV文件
    import csv
    with open('genshin_characters.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['id', 'name', 'rarity', 'element', 'weapon', 'detail_url', 'image_url']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(characters)
