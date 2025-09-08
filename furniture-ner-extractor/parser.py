"""
Module for web page parsing and extraction of text content and structured data
Supports multiple data formats including JSON-LD, microdata, and meta tags
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import List, Optional, Dict
from urllib.parse import urlparse

def get_page_text(url: str) -> Optional[str]:
    """Extracts and cleans text content from a web page with proper error handling"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }

        # Fetch webpage with timeout and headers
        response = requests.get(url, timeout=15, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove non-content elements for cleaner text extraction
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()

        # Extract text content with proper spacing
        text = soup.get_text(" ", strip=True)
        
        # Clean and normalize text content
        text = re.sub(r'\s+', ' ', text)  # Collapse multiple spaces
        text = re.sub(r'[^\w\s.,!?$-]', ' ', text)  # Remove special characters
        
        return text if text.strip() else None

    except requests.exceptions.RequestException as e:
        print(f"Network error while parsing {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error parsing {url}: {e}")
        return None

def parse_structured_data(url: str) -> List[str]:
    """Extracts structured data from webpage including JSON-LD, microdata, and meta tags"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        products = []

        # Extract from JSON-LD structured data
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0]  # Handle arrays of structured data

                # Extract product information from structured data
                products.extend(extract_from_structured_data(data))

            except json.JSONDecodeError:
                continue  # Skip invalid JSON
            except Exception as e:
                print(f"Error processing JSON-LD data: {e}")
                continue

        # Extract from meta tags and Open Graph
        meta_products = extract_from_meta_tags(soup)
        products.extend(meta_products)

        # Return unique products only
        return list(set(products))

    except requests.exceptions.RequestException as e:
        print(f"Network error fetching structured data: {e}")
        return []
    except Exception as e:
        print(f"Error extracting structured data: {e}")
        return []

def extract_from_structured_data(data: Dict) -> List[str]:
    """Recursively extracts product names from structured data objects"""
    products = []
    
    if isinstance(data, dict):
        # Handle Product schema types
        if data.get("@type") in ["Product", "IndividualProduct"]:
            if name := data.get("name"):
                products.append(str(name))
        
        # Handle ItemList schema (product listings)
        elif data.get("@type") == "ItemList":
            if items := data.get("itemListElement"):
                for item in items:
                    if isinstance(item, dict) and "name" in item:
                        products.append(str(item["name"]))
        
        # Handle BreadcrumbList schema (navigation elements)
        elif data.get("@type") == "BreadcrumbList":
            if items := data.get("itemListElement"):
                for item in items:
                    if isinstance(item, dict) and "name" in item:
                        products.append(str(item["name"]))
        
        # Recursively search nested structures
        for value in data.values():
            if isinstance(value, (dict, list)):
                products.extend(extract_from_structured_data(value))
    
    elif isinstance(data, list):
        for item in data:
            products.extend(extract_from_structured_data(item))
    
    return products

def extract_from_meta_tags(soup: BeautifulSoup) -> List[str]:
    """Extracts product information from meta tags and page metadata"""
    products = []
    
    # Open Graph title extraction
    if og_title := soup.find("meta", property="og:title"):
        if content := og_title.get("content"):
            products.append(content)
    
    # Twitter card title extraction
    if twitter_title := soup.find("meta", name="twitter:title"):
        if content := twitter_title.get("content"):
            products.append(content)
    
    # Meta description with furniture-related keywords
    if description := soup.find("meta", attrs={"name": "description"}):
        if content := description.get("content"):
            furniture_keywords = ["chair", "table", "sofa", "bed", "диван", "стол", "кровать"]
            if any(keyword in content.lower() for keyword in furniture_keywords):
                products.append(content)
    
    # Page title extraction
    if title_tag := soup.find("title"):
        title_text = title_tag.get_text(strip=True)
        if title_text and len(title_text) > 5:  # Filter short titles
            products.append(title_text)
    
    return products

def is_valid_url(url: str) -> bool:
    """Validates URL format and structure"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
    except Exception:
        return False
