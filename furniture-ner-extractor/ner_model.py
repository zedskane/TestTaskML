"""
Модуль для извлечения названий товаров с помощью NER модели и ключевых слов
Комбинированный подход для максимальной эффективности
"""

from transformers import pipeline
import re
from typing import List, Optional

# Глобальные переменные для кэширования модели
_ner_model = None
_furniture_keywords = None

def get_ner_model():
    """Ленивая загрузка NER модели"""
    global _ner_model
    if _ner_model is None:
        try:
            _ner_model = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple",
                device=-1  # Использовать CPU
            )
        except Exception as e:
            print(f"Ошибка загрузки NER модели: {e}")
            _ner_model = None
    return _ner_model

def get_furniture_keywords():
    """Ключевые слова для мебельной тематики"""
    global _furniture_keywords
    if _furniture_keywords is None:
        _furniture_keywords = [
            # English keywords
            "sofa", "chair", "table", "bed", "desk", "lamp", "mirror", "cabinet",
            "shelf", "ottoman", "bench", "stool", "dresser", "nightstand", "bookcase",
            "wardrobe", "dining", "living", "bedroom", "office", "kitchen", "bathroom",
            "outdoor", "light", "lighting", "pendant", "ceiling", "wall", "floor",
            "mattress", "pillow", "cushion", "throw", "rug", "curtain", "blind",
            "furniture", "collection", "series", "set", "armchair", "recliner",
            "sectional", "loveseat", "console", "coffee", "side", "accents",
            
            # Russian keywords
            "диван", "стул", "стол", "кровать", "кресло", "лампа", "зеркало", "шкаф",
            "полка", "пуф", "скамья", "табурет", "комод", "тумба", "стеллаж", "гардероб",
            "столовая", "гостиная", "спальня", "офис", "кухня", "ванная", "уличная",
            "свет", "освещение", "подвесной", "потолочный", "настенный", "напольный",
            "матрас", "подушка", "подушка", "ковер", "штора", "жалюзи", "мебель",
            "коллекция", "серия", "комплект", "кресло", "раскладушка", "угловой"
        ]
    return _furniture_keywords

def extract_products(text: str) -> List[str]:
    """Извлекает названия товаров из текста с помощью NER модели"""
    if not text or not text.strip():
        return []

    products = []
    model = get_ner_model()
    
    if model is None:
        return products

    try:
        # Обрабатываем первые 2000 символов для скорости
        short_text = text[:2000]
        entities = model(short_text)

        for entity in entities:
            word = entity.get('word', '').strip()
            score = entity.get('score', 0.0)
            entity_type = entity.get('entity_group', '')

            # Фильтруем по score и типу сущности
            if (score > 0.5 and entity_type in ['ORG', 'PRODUCT', 'MISC'] and
                len(word) > 2 and not word.isdigit()):
                # Очищаем слово
                clean_word = re.sub(r'[^\w\s\-]', '', word)
                if len(clean_word) > 2:
                    products.append(clean_word)

    except Exception as e:
        print(f"Ошибка NER обработки: {e}")

    return products

def analyze_text_with_keywords(text: str) -> List[str]:
    """Анализ текста с помощью ключевых слов мебельной тематики"""
    if not text:
        return []

    products = []
    keywords = get_furniture_keywords()
    text_lower = text.lower()

    try:
        # Поиск предложений с ключевыми словами
        sentences = re.split(r'[.!?]', text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Проверяем наличие ключевых слов в предложении
            found_keywords = [
                keyword for keyword in keywords 
                if keyword in sentence_lower and len(keyword) > 2
            ]
            
            if found_keywords:
                # Очищаем предложение и добавляем как потенциальный продукт
                clean_sentence = re.sub(r'\s+', ' ', sentence).strip()
                if 10 <= len(clean_sentence) <= 150:
                    products.append(clean_sentence)

        # Поиск отдельных слов, содержащих ключевые слова
        words = re.findall(r'\b\w+\b', text)
        for word in words:
            word_lower = word.lower()
            if any(keyword in word_lower for keyword in keywords):
                if len(word) > 3 and not word.isdigit():
                    products.append(word)

    except Exception as e:
        print(f"Ошибка keyword анализа: {e}")

    return products

def combined_extraction(text: str) -> List[str]:
    """Комбинированное извлечение продуктов"""
    ner_results = extract_products(text)
    keyword_results = analyze_text_with_keywords(text)
    
    all_results = ner_results + keyword_results
    unique_results = list(set(all_results))
    
    return unique_results
