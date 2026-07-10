from langchain_community.document_loaders import SeleniumURLLoader
from openai import OpenAI
from typing import List
import os
from dotenv import load_dotenv
load_dotenv()

def scrape_pages(urls: List[str]) -> dict:
    """
    Scrape content from a list of URLs using Selenium.
    
    Args:
        urls: List of URLs to scrape
        
    Returns:
        Dictionary containing structured menu data with 'items' key
    """
    print(f"Scraping pages: {urls}")
    try:
        loader = SeleniumURLLoader(urls=urls)
        data = loader.load()  # list of langchain_core.documents.base.Document objects
        print('Data',data)
        if not data:
            print("No data scraped from URLs")
            return {"items": []}
            
        # Combine all page content into a single string
        combined_content = "\n\n".join([doc.page_content for doc in data])
        print('COmbined Document',combined_content)
        return combined_content
        
    except Exception as e:
        print(f"Error scraping pages: {e}")
        return {"items": []}

if __name__ == "__main__":
    urls = ["https://mcdonalds.com.pk/product/omelette-mcmuffin-meal/"]
    data = scrape_pages(urls)

    with open('tests/scrapper/sample.txt', 'w') as f:
        f.write(data)