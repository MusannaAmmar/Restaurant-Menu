import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import json
from playwright.sync_api import sync_playwright

def scrape_page(url: str) -> dict:
    def parse_html(html, base_url):
        soup = BeautifulSoup(html, "html.parser")

        texts = [tag.get_text(strip=True) for tag in soup.find_all(["p", "h1", "h2", "h3", "li"]) if tag.get_text(strip=True)]
        images = [urljoin(base_url, img["src"]) for img in soup.find_all("img", src=True)]

        # Extract JSON from <script> tags
        json_data = []
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                json_data.append(json.loads(script.string))
            except:
                pass

        return {"text": texts, "media": {"images": images}, "json": json_data}

    # First try static request
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        data = parse_html(resp.text, url)
        if data["text"] or data["media"]["images"] or data["json"]:
            return data
    except:
        pass

    # Fallback to Playwright
    try:
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            html = page.content()
            browser.close()
        return parse_html(html, url)
    except Exception as e:
        return {"error": str(e)}

data = scrape_page("https://www.kfcpakistan.com/menu#Promotion")