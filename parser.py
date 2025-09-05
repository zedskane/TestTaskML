"""
Модуль для парсинга веб-страниц и извлечения текста и структурированных данных
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List, Optional, Dict
from urllib.parse import urlparse

def get_page_text(url: str) -> Optional[str]:
    """Парсит текст со страницы"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Удаляем ненужные теги
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        # Извлекаем текст
        text = soup.get_text(" ", strip=True)
        
        # Очищаем текст
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?$-]', ' ', text)
        
        return text if text.strip() else None

    except Exception as e:
        print(f"Ошибка при парсинге {url}: {e}")
        return None

def parse_structured_data(url: str) -> List[str]:
    """Извлекает структурированные данные (JSON-LD, Microdata)"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        products = []

        # JSON-LD данные
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]

                # Извлекаем продукты из структурированных данных
                products.extend(extract_from_structured_data(data))

            except json.JSONDecodeError:
                continue

        # Open Graph и meta tags
        meta_products = extract_from_meta_tags(soup)
        products.extend(meta_products)

        return list(set(products))

    except Exception as e:
        print(f"Ошибка при извлечении структурированных данных: {e}")
        return []

def extract_from_structured_data(data: Dict) -> List[str]:
    """Извлекает продукты из структурированных данных"""
    products = []
    
    if isinstance(data, dict):
        # Product data
        if data.get("@type") in ["Product", "IndividualProduct"]:
            if name := data.get("name"):
                products.append(str(name))
        
        # ItemList data
        elif data.get("@type") == "ItemList":
            if items := data.get("itemListElement"):
                for item in items:
                    if isinstance(item, dict) and "name" in item:
                        products.append(str(item["name"]))
        
        # BreadcrumbList
        elif data.get("@type") == "BreadcrumbList":
            if items := data.get("itemListElement"):
                for item in items:
                    if isinstance(item, dict) and "name" in item:
                        products.append(str(item["name"]))
        
        # Рекурсивный поиск в глубину
        for value in data.values():
            if isinstance(value, (dict, list)):
                products.extend(extract_from_structured_data(value))
    
    elif isinstance(data, list):
        for item in data:
            products.extend(extract_from_structured_data(item))
    
    return products

def extract_from_meta_tags(soup: BeautifulSoup) -> List[str]:
    """Извлекает информацию из meta тегов"""
    products = []
    
    # Open Graph title
    if og_title := soup.find("meta", property="og:title"):
        if content := og_title.get("content"):
            products.append(content)
    
    # Twitter title
    if twitter_title := soup.find("meta", name="twitter:title"):
        if content := twitter_title.get("content"):
            products.append(content)
    
    # Meta description с ключевыми словами
    if description := soup.find("meta", attrs={"name": "description"}):
        if content := description.get("content"):
            if any(keyword in content.lower() for keyword in ["chair", "table", "sofa", "bed", "диван", "стол", "кровать"]):
                products.append(content)
    
    # Title страницы
    if title_tag := soup.find("title"):
        title_text = title_tag.get_text(strip=True)
        if title_text and len(title_text) > 5:
            products.append(title_text)
    
    return products

def is_valid_url(url: str) -> bool:
    """Проверяет валидность URL"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
