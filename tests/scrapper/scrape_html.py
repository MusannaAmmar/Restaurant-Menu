from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import tempfile
import os
import shutil

def _detect_chrome_binary():
    # Try environment variables first, then common paths/which results
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
    ]
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    return None

def scrape_website_html(url, output_file):
    """
    Simple function to scrape HTML from a website using Selenium
    """
    # Create a unique temporary directory for user data
    temp_dir = tempfile.mkdtemp(prefix="chrome_user_data_")
    
    # Set up Chrome options for server environment
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")
    chrome_options.add_argument(f"--user-data-dir={temp_dir}")
    chrome_options.add_argument("--remote-debugging-port=0")  # Use random port
    # Detect Chrome/Chromium binary on the system
    chrome_binary = _detect_chrome_binary()
    if chrome_binary:
        chrome_options.binary_location = chrome_binary
    else:
        print("Chrome/Chromium not found. Install google-chrome or chromium-browser and try again.")
        return
    
    # Initialize the driver with webdriver-manager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Navigate to the website
        print(f"Loading {url}...")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Get the complete HTML
        html_content = driver.page_source
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTML saved to {output_file}")
        print(f"HTML length: {len(html_content)} characters")
        
    except Exception as e:
        print(f"Error occurred: {e}")
    
    finally:
        # Close the driver
        driver.quit()
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

if __name__ == "__main__":
    # Hard-coded URL as requested
    url = "https://www.starbucks.com"
    output_file = "starbucks_html.html"
    
    scrape_website_html(url, output_file)
