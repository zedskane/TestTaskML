"""
Главное приложение для извлечения названий продуктов с веб-сайтов мебельных магазинов
FastAPI приложение с HTML интерфейсом
"""

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from parser import get_page_text, parse_structured_data
from ner_model import extract_products, analyze_text_with_keywords

app = FastAPI(
    title="Furniture Product Extractor",
    description="Система для извлечения названий товаров с сайтов мебельных магазинов",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Настройка шаблонов
templates = Jinja2Templates(directory="templates")

# Подключение статических файлов
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница с формой для ввода URL"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "products": None,
        "error": None,
        "url": ""
    })

@app.post("/extract", response_class=HTMLResponse)
async def extract_products_route(request: Request, url: str = Form(...)):
    """Извлечение товаров с указанного URL"""
    try:
        if not url.startswith(('http://', 'https://')):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "products": [],
                "error": "URL должен начинаться с http:// или https://",
                "url": url
            })

        # Получаем текст и структурированные данные
        text = get_page_text(url)
        structured_data = parse_structured_data(url)
        
        if not text and not structured_data:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "products": [],
                "error": "Не удалось получить данные со страницы",
                "url": url
            })

        # Извлекаем продукты разными методами
        all_products = []
        
        # Из структурированных данных
        if structured_data:
            all_products.extend(structured_data)
        
        # Из текста через NER
        if text:
            ner_products = extract_products(text)
            all_products.extend(ner_products)
            
            # Дополнительный анализ по ключевым словам
            keyword_products = analyze_text_with_keywords(text)
            all_products.extend(keyword_products)

        # Убираем дубликаты и пустые значения
        unique_products = list(set(
            product.strip() for product in all_products 
            if product and len(product.strip()) > 2
        ))

        # Сортируем по длине (обычно более длинные названия - более конкретные продукты)
        unique_products.sort(key=len, reverse=True)

        return templates.TemplateResponse("index.html", {
            "request": request,
            "products": unique_products[:20],  # Ограничиваем количество
            "error": None,
            "url": url,
            "products_count": len(unique_products)
        })

    except Exception as e:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "products": [],
            "error": f"Произошла ошибка: {str(e)}",
            "url": url
        })

@app.get("/api/extract")
async def api_extract(url: str):
    """API endpoint для извлечения продуктов"""
    try:
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        text = get_page_text(url)
        structured_data = parse_structured_data(url)
        
        all_products = []
        
        if structured_data:
            all_products.extend(structured_data)
        
        if text:
            ner_products = extract_products(text)
            all_products.extend(ner_products)
            
            keyword_products = analyze_text_with_keywords(text)
            all_products.extend(keyword_products)

        unique_products = list(set(
            product.strip() for product in all_products 
            if product and len(product.strip()) > 2
        ))

        return {
            "success": True,
            "url": url,
            "products_count": len(unique_products),
            "products": unique_products[:20],
            "methods_used": [
                "structured_data" if structured_data else None,
                "ner_model" if text else None,
                "keyword_analysis" if text else None
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
