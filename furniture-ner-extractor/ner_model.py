"""
Module for extracting product names using NER model and keyword analysis
Combined approach for maximum effectiveness in furniture product recognition
"""

from transformers import pipeline
import re
from typing import List, Optional

# Global variables for model caching
_ner_model = None
_furniture_keywords = None

def get_ner_model():
    """Lazy loading of NER model to optimize resource usage"""
    global _ner_model
    if _ner_model is None:
        try:
            _ner_model = pipeline(
                "ner",
                model="dslim/bert-base-NER",
                aggregation_strategy="simple",
                device=-1  # Use CPU for compatibility
            )
        except Exception as e:
            print(f"Error loading NER model: {e}")
            _ner_model = None
    return _ner_model

def get_furniture_keywords():
    """Comprehensive furniture-related keywords for product identification"""
    global _furniture_keywords
    if _furniture_keywords is None:
        _furniture_keywords = [
            # English furniture keywords
            "sofa", "chair", "table", "bed", "desk", "lamp", "mirror", "cabinet",
            "shelf", "ottoman", "bench", "stool", "dresser", "nightstand", "bookcase",
            "wardrobe", "dining", "living", "bedroom", "office", "kitchen", "bathroom",
            "outdoor", "light", "lighting", "pendant", "ceiling", "wall", "floor",
            "mattress", "pillow", "cushion", "throw", "rug", "curtain", "blind",
            "furniture", "collection", "series", "set", "armchair", "recliner",
            "sectional", "loveseat", "console", "coffee", "side", "accents",
            
            # Russian furniture keywords
            "диван", "стул", "стол", "кровать", "кресло", "лампа", "зеркало", "шкаф",
            "полка", "пуф", "скамья", "табурет", "комод", "тумба", "стеллаж", "гардероб",
            "столовая", "гостиная", "спальня", "офис", "кухня", "ванная", "уличная",
            "свет", "освещение", "подвесной", "потолочный", "настенный", "напольный",
            "матрас", "подушка", "подушка", "ковер", "штора", "жалюзи", "мебель",
            "коллекция", "серия", "комплект", "кресло", "раскладушка", "угловой"
        ]
    return _furniture_keywords

def extract_products(text: str) -> List[str]:
    """Extract product names from text using NER model with entity recognition"""
    if not text or not text.strip():
        return []

    products = []
    model = get_ner_model()
    
    if model is None:
        return products

    try:
        # Process first 2000 characters for performance optimization
        short_text = text[:2000]
        entities = model(short_text)

        for entity in entities:
            word = entity.get('word', '').strip()
            score = entity.get('score', 0.0)
            entity_type = entity.get('entity_group', '')

            # Filter entities by confidence score and relevant types
            if (score > 0.5 and entity_type in ['ORG', 'PRODUCT', 'MISC'] and
                len(word) > 2 and not word.isdigit()):
                # Clean special characters while preserving hyphens
                clean_word = re.sub(r'[^\w\s\-]', '', word)
                if len(clean_word) > 2:
                    products.append(clean_word)

    except Exception as e:
        print(f"NER processing error: {e}")

    return products

def analyze_text_with_keywords(text: str) -> List[str]:
    """Analyze text using furniture-specific keyword matching and context extraction"""
    if not text:
        return []

    products = []
    keywords = get_furniture_keywords()
    text_lower = text.lower()

    try:
        # Split text into sentences for contextual analysis
        sentences = re.split(r'[.!?]', text)
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            
            # Identify sentences containing relevant furniture keywords
            found_keywords = [
                keyword for keyword in keywords 
                if keyword in sentence_lower and len(keyword) > 2
            ]
            
            if found_keywords:
                # Clean and validate potential product sentences
                clean_sentence = re.sub(r'\s+', ' ', sentence).strip()
                if 10 <= len(clean_sentence) <= 150:
                    products.append(clean_sentence)

        # Extract individual words containing furniture keywords
        words = re.findall(r'\b\w+\b', text)
        for word in words:
            word_lower = word.lower()
            if any(keyword in word_lower for keyword in keywords):
                if len(word) > 3 and not word.isdigit():
                    products.append(word)

    except Exception as e:
        print(f"Keyword analysis error: {e}")

    return products

def combined_extraction(text: str) -> List[str]:
    """Combine NER and keyword extraction methods for comprehensive product identification"""
    ner_results = extract_products(text)
    keyword_results = analyze_text_with_keywords(text)
    
    # Merge and deduplicate results from both methods
    all_results = ner_results + keyword_results
    unique_results = list(set(all_results))
    
    return unique_results
