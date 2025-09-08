```python
"""
Main application for extracting product names from furniture store websites
FastAPI application with HTML interface
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
    description="System for extracting product names from furniture store websites",
    version="1.0.0"
)

# CORS middleware configuration to allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (adjust for production)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Setup Jinja2 templates for HTML rendering
templates = Jinja2Templates(directory="templates")

# Static files mounting (commented out but available for future use)
# app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with URL input form for product extraction"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "products": None,
        "error": None,
        "url": ""
    })

@app.post("/extract", response_class=HTMLResponse)
async def extract_products_route(request: Request, url: str = Form(...)):
    """Extract products from the provided URL and display results"""
    try:
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return templates.TemplateResponse("index.html", {
                "request": request,
                "products": [],
                "error": "URL must start with http:// or https://",
                "url": url
            })

        # Fetch page content and structured data
        text = get_page_text(url)
        structured_data = parse_structured_data(url)
        
        # Check if any data was retrieved
        if not text and not structured_data:
            return templates.TemplateResponse("index.html", {
                "request": request,
                "products": [],
                "error": "Failed to retrieve data from the page",
                "url": url
            })

        # Extract products using multiple methods
        all_products = []
        
        # Add products from structured data (JSON-LD, microdata, etc.)
        if structured_data:
            all_products.extend(structured_data)
        
        # Extract products using NER model from page text
        if text:
            ner_products = extract_products(text)
            all_products.extend(ner_products)
            
            # Additional extraction using keyword analysis
            keyword_products = analyze_text_with_keywords(text)
            all_products.extend(keyword_products)

        # Remove duplicates and empty values, clean whitespace
        unique_products = list(set(
            product.strip() for product in all_products 
            if product and len(product.strip()) > 2  # Filter out short strings
        ))

        # Sort by length (longer names tend to be more specific products)
        unique_products.sort(key=len, reverse=True)

        return templates.TemplateResponse("index.html", {
            "request": request,
            "products": unique_products[:20],  # Limit to top 20 results
            "error": None,
            "url": url,
            "products_count": len(unique_products)
        })

    except Exception as e:
        # Handle any unexpected errors
        return templates.TemplateResponse("index.html", {
            "request": request,
            "products": [],
            "error": f"An error occurred: {str(e)}",
            "url": url
        })

@app.get("/api/extract")
async def api_extract(url: str):
    """API endpoint for programmatic product extraction"""
    try:
        # Validate URL format for API
        if not url.startswith(('http://', 'https://')):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        
        # Extract data using multiple methods
        text = get_page_text(url)
        structured_data = parse_structured_data(url)
        
        all_products = []
        
        # Add structured data products
        if structured_data:
            all_products.extend(structured_data)
        
        # Add NER and keyword-based products
        if text:
            ner_products = extract_products(text)
            all_products.extend(ner_products)
            
            keyword_products = analyze_text_with_keywords(text)
            all_products.extend(keyword_products)

        # Process and clean results
        unique_products = list(set(
            product.strip() for product in all_products 
            if product and len(product.strip()) > 2
        ))

        # Return structured JSON response
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
        # Return error details in API response
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint for API monitoring and diagnostics"""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    # Run the FastAPI application with Uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=8000)
```
