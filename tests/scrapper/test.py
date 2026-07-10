import sys
import os

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from app.helpers.url_extractor import extract_urls_from_website
from app.helpers.filter import filter_menu_related_urls

urls = extract_urls_from_website("https://www.subway.com")
print(len(urls))

urls = filter_menu_related_urls(urls)
print(len(urls))
print(urls)