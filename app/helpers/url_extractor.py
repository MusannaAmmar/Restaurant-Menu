

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from urllib.parse import urljoin, urlparse
import os
import shutil
import tempfile

from pydantic import BaseModel
from typing import List
import os
import json

class UrlListSchema(BaseModel):
    urls: List[str]

class ImageListSchema(BaseModel):
    images: List[dict]  # List of {"url": str, "alt": str, "title": str}

def _detect_chrome_binary():
    """Try to locate a Chrome/Chromium binary on the system."""
    candidates = [
        os.environ.get("GOOGLE_CHROME_BIN"),
        os.environ.get("CHROME_BIN"),
        shutil.which("google-chrome"),
        shutil.which("google-chrome-stable"),
        shutil.which("chromium-browser"),
        shutil.which("chromium"),
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
        "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",  # Windows
        "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",  # Windows 32-bit
    ]
    
    print("Looking for Chrome binary...")
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            print(f"✓ Found Chrome at: {candidate}")
            return candidate
    
    print("✗ No Chrome binary found!")
    return None

def is_internal_url(url, base_domain):
    """Check if URL is internal to the website"""
    try:
        parsed = urlparse(url)
        return parsed.netloc == base_domain or parsed.netloc == ""
    except:
        return False


async def extract_urls_from_website(website_url, debug=True):
    """
    Extract all internal URLs and images from a given website.
    
    Args:
        website_url (str): The website URL to crawl
        debug (bool): Enable debug output
    
    Returns:
        dict: Dictionary containing 'urls' list and 'images' list
    """
    driver = None
    temp_dir = None
    
    try:
        if debug:
            print(f"\n{'='*60}")
            print(f"Starting extraction for: {website_url}")
            print(f"{'='*60}\n")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="chrome_user_data_")
        if debug:
            print(f"Created temp directory: {temp_dir}")

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # Detect Chrome binary
        chrome_binary = _detect_chrome_binary()
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
        else:
            print("\n⚠️  ERROR: Chrome/Chromium not found!")
            print("Please install Chrome or set CHROME_BIN environment variable")
            return {"urls": [], "images": [], "error": "Chrome not found"}
        
        # Initialize driver
        if debug:
            print("Initializing Chrome driver...")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        if debug:
            print(f"✓ Chrome driver initialized")
            print(f"Loading page: {website_url}")
        
        driver.get(website_url)
        
        # Wait for page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        if debug:
            print("✓ Page loaded")
            print(f"Page title: {driver.title}")
        
        # Wait for JavaScript
        time.sleep(5)
        
        # Scroll to trigger lazy loading
        if debug:
            print("Scrolling to load lazy content...")
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
        
        # Get base domain
        base_domain = urlparse(website_url).netloc
        if debug:
            print(f"Base domain: {base_domain}")
        
        urls = set()
        images_data = []
        found_images = set()
        
        # Extract all links
        if debug:
            print("\n--- Extracting URLs ---")
        
        links = driver.find_elements(By.TAG_NAME, "a")
        if debug:
            print(f"Found {len(links)} <a> tags")
        
        for link in links:
            try:
                href = link.get_attribute("href")
                if href:
                    # Convert to absolute URL
                    if href.startswith('/'):
                        absolute_url = urljoin(website_url, href)
                    elif not href.startswith('http'):
                        absolute_url = urljoin(website_url, href)
                    else:
                        absolute_url = href
                    
                    # Only include internal URLs
                    if is_internal_url(absolute_url, base_domain):
                        urls.add(absolute_url)
            except Exception as e:
                if debug:
                    print(f"Error processing link: {e}")
                continue
        
        if debug:
            print(f"✓ Extracted {len(urls)} internal URLs")
        
        # Extract images
        if debug:
            print("\n--- Extracting Images ---")
        
        # Try multiple strategies
        img_selectors = [
            "//img",  # All images
            "//picture//img",  # Picture elements
            "//div[contains(@class, 'image')]//img",  # Images in containers
            "//*[@style[contains(., 'background-image')]]",  # Background images
        ]
        
        all_img_elements = []
        for selector in img_selectors:
            try:
                elements = driver.find_elements(By.XPATH, selector)
                if debug and elements:
                    print(f"Selector '{selector}': found {len(elements)} elements")
                all_img_elements.extend(elements)
            except Exception as e:
                if debug:
                    print(f"Error with selector '{selector}': {e}")
        
        if debug:
            print(f"Total image elements found: {len(all_img_elements)}")
        
        for img in all_img_elements:
            try:
                # Try multiple attributes
                img_src = (img.get_attribute("src") or 
                          img.get_attribute("data-src") or 
                          img.get_attribute("data-lazy-src") or
                          img.get_attribute("data-original"))
                
                # Check background images
                if not img_src:
                    style = img.get_attribute("style")
                    if style and "background-image" in style:
                        import re
                        match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                        if match:
                            img_src = match.group(1)
                
                if img_src and img_src not in found_images:
                    # Skip data URIs and tiny images
                    if 'data:image' in img_src or len(img_src) < 10:
                        continue
                    
                    # Convert to absolute URL
                    if img_src.startswith('//'):
                        absolute_img_url = 'https:' + img_src
                    elif img_src.startswith('/'):
                        absolute_img_url = urljoin(website_url, img_src)
                    elif not img_src.startswith('http'):
                        absolute_img_url = urljoin(website_url, img_src)
                    else:
                        absolute_img_url = img_src
                    
                    found_images.add(img_src)
                    
                    images_data.append({
                        "url": absolute_img_url,
                        "alt": img.get_attribute("alt") or "",
                        "title": img.get_attribute("title") or ""
                    })
                    
                    if debug:
                        print(f"  ✓ {absolute_img_url[:80]}...")
                        
            except Exception as e:
                if debug:
                    print(f"Error processing image: {e}")
                continue
        
        # Results
        clean_urls = sorted(list(urls))
        
        if debug:
            print(f"\n{'='*60}")
            print(f"RESULTS:")
            print(f"  URLs: {len(clean_urls)}")
            print(f"  Images: {len(images_data)}")
            print(f"{'='*60}\n")
        
        result = {
            "urls": clean_urls,
            "images": images_data
        }
        
        return result
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"urls": [], "images": [], "error": str(e)}
        
    finally:
        if driver:
            driver.quit()
            if debug:
                print("✓ Browser closed")
        
        # Clean up temp directory
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                if debug:
                    print("✓ Temp directory cleaned")
            except Exception as e:
                if debug:
                    print(f"Warning: Could not clean temp directory: {e}")

