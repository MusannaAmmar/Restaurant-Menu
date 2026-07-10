
from langchain_community.document_loaders import SeleniumURLLoader
from openai import OpenAI
from pydantic import BaseModel
from typing import List
import os
from app.base_models.menu import MenusSchema
import tempfile
from app.helpers.url_extractor import extract_urls_from_website
from app.helpers.filter import filter_menu_related_urls
import json


# @time_function('structured_output')
async def get_structured_output(text: str, extracted_images: List[dict] = None):
    """
    Extract structured menu data from text content.
    
    Args:
        text: The scraped content
        extracted_images: List of image dictionaries from extract_urls_from_website
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Prepare image information to help the AI
    image_context = ""
    if extracted_images:
        image_context = "\n\n" + "="*60 + "\nAVAILABLE IMAGES FROM WEBSITE:\n" + "="*60 + "\n"
        for i, img in enumerate(extracted_images, 1):
            image_context += f"\n[IMAGE {i}]\n"
            image_context += f"URL: {img['url']}\n"
            if img.get('alt'):
                image_context += f"Alt text: {img['alt']}\n"
            if img.get('title'):
                image_context += f"Title: {img['title']}\n"
            if img.get('context'):
                image_context += f"Context: {img['context'][:100]}\n"
        
        image_context += (
            "\n" + "="*60 + "\n"
            "IMAGE MATCHING RULES:\n"
            "1. Match each menu item with [IMAGE X] from the list above\n"
            "2. Use alt text, title, URL patterns, and context to find the correct image\n"
            "3. Item name must closely match the alt text or context\n"
            "4. DO NOT use promotional banner images (banners, desktop_image, etc.)\n"
            "5. DO NOT use the same image for multiple different items\n"
            "6. If uncertain about a match, leave images array empty for that item\n"
            "7. Only use images that clearly show the specific food item\n"
            "8. Promotional images showing multiple items should NOT be used for individual items\n"
            + "="*60 + "\n"
        )
    
    
    system_prompt = (
        "Extract restaurant menu information from the provided text and output valid JSON matching this schema: "
        f"{MenusSchema.model_json_schema()}\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. EXTRACT PRICES: Look for all price information (e.g., $12.99, Rs. 500, etc.) associated with each menu item\n"
        "2. Include the price in the 'price' field for each item\n"
        "3. Extract prices in their original currency/format as shown on the website\n"
        "4. If an item has multiple sizes/variants with different prices, create separate items or note in description\n"
        "\nCRITICAL INSTRUCTIONS FOR IMAGE EXTRACTION:\n"
        "1. YOU MUST USE the image URLs provided in the 'AVAILABLE IMAGES' section\n"
        "2. Match each menu item with its corresponding image(s) from the provided list\n"
        "3. Use alt text, titles, and context to match images to items\n"
        "4. Include the COMPLETE image URL in the 'images' array for each item\n"
        "5. If an image clearly relates to a menu item (based on alt/title), include it\n"
        "6. Each menu item should have at least one image if available\n"
        "7. DO NOT invent image URLs - only use URLs from the AVAILABLE IMAGES list\n"
        "8. If multiple images match an item, include all relevant ones\n"
        f"{image_context}"
    )
    
    
    response = client.beta.chat.completions.parse(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        response_format=MenusSchema,
    )
    
    return response.choices[0].message.parsed.model_dump()



# @time_function('scrape_page')
async def scrape_pages(urls: List[str]) -> dict:
    """
    Scrape content from a list of URLs using Selenium.
    
    Args:
        urls: List of URLs to scrape
        
    Returns:
        Dictionary containing structured menu data with 'menus' key
    """
    final_urls = []
    all_extracted_images = []  # Store all images from extraction
    
    # Extract URLs and images from each provided URL
    for url in urls:
        print(f"\n{'='*60}")
        print(f"Processing: {url}")
        print(f"{'='*60}")
        
        # Step 1: Extract URLs and images from the website
        print("Step 1: Extracting URLs and images...")
        extraction_result = await extract_urls_from_website(url)
        
        # Check if extraction returned an error
        if "error" in extraction_result:
            print(f"  ⚠️  Extraction error: {extraction_result['error']}")
            continue
        
        # Step 2: Get the extracted URLs
        extracted_urls = extraction_result.get("urls", [])
        extracted_images = extraction_result.get("images", [])
        
        print(f"  ✓ Found {len(extracted_urls)} URLs")
        print(f"  ✓ Found {len(extracted_images)} images")
        
        # Step 3: Filter both URLs and images using AI
        if extracted_urls or extracted_images:
            print("\nStep 2: Filtering menu-related URLs and images with AI...")
            
            # Option 1: Use the combined filter (filters both URLs and images)
            # from app.helpers.filter import filter_extraction_result
            # filtered_result = filter_extraction_result(extraction_result)
            # filtered_urls = filtered_result["urls"]
            # filtered_images = filtered_result["images"]
            
            # Option 2: Use separate filters (your current approach)
            filtered_urls = await filter_menu_related_urls(extraction_result)
            filtered_images = extracted_images  # Or filter these too if needed
            
            print(f"  ✓ Filtered to {len(filtered_urls)} menu-related URLs")
            final_urls.extend(filtered_urls)
            
            if filtered_images:
                print(f"  ✓ Collected {len(filtered_images)} food images")
                all_extracted_images.extend(filtered_images)
            
            # Show sample images
            for i, img in enumerate(extracted_images[:3], 1):
                print(f"  {i}. {img['url'][:80]}...")
                if img.get('alt'):
                    print(f"     Alt: {img['alt']}")
    
    # Add original URLs to final list
    final_urls.extend(urls)
    
    # Remove duplicates while preserving order
    final_urls = list(dict.fromkeys(final_urls))
    
    print(f"\n{'='*60}")
    print(f"EXTRACTION SUMMARY:")
    print(f"  Total URLs to scrape: {len(final_urls)}")
    print(f"  Total images collected: {len(all_extracted_images)}")
    print(f"{'='*60}\n")
    
    if not final_urls:
        print("⚠️  No URLs to scrape!")
        return {"menus": []}
    
    try:
        tmpdir = tempfile.mkdtemp()
        
        print("Step 4: Scraping pages with Selenium...")
        loader = SeleniumURLLoader(
            urls=final_urls,
            headless=True,
            browser="chrome",
            arguments=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                f"--user-data-dir={tmpdir}"
            ],
        )
        
        data = loader.load()
        
        if not data:
            print("⚠️  No data scraped from URLs")
            return {"menus": []}
        
        print(f"✓ Successfully scraped {len(data)} pages\n")
        
        # Combine all page content
        combined_content = ""
        
        # Add metadata about the pages scraped
        page_info = "SCRAPED PAGES:\n"
        for i, doc in enumerate(data, 1):
            # print('Documents text',doc.page_content)
            source_url = doc.metadata.get('source', 'Unknown URL')
            page_info += f"{i}. {source_url}\n"
            combined_content += f"\n\n--- Content from: {source_url} ---\n{doc.page_content}"
        
        full_content = f"{page_info}\n\n{combined_content}"
        
        print(f"Step 5: Processing content with AI...")
        print(f"  Content length: {len(full_content):,} characters")
        print(f"  Images to match: {len(all_extracted_images)}")
        
        # Pass both content and extracted images to the AI
        structured_data = await get_structured_output(full_content[:2500], all_extracted_images)
        
        # Debug output
        if structured_data and structured_data.get("menus"):
            total_items = sum(len(menu.get("items", [])) for menu in structured_data["menus"])
            items_with_images = sum(
                1 for menu in structured_data["menus"] 
                for item in menu.get("items", []) 
                if item.get("images") and len(item.get("images", [])) > 0
            )
            
            print(f"\n{'='*60}")
            print(f"EXTRACTION RESULTS:")
            print(f"  Menus extracted: {len(structured_data['menus'])}")
            print(f"  Total menu items: {total_items}")
            print(f"  Items with images: {items_with_images}/{total_items}")
            
            # Show sample of extracted items
            print(f"\n  Sample items:")
            item_count = 0
            for menu in structured_data["menus"][:2]:  # First 2 menus
                for item in menu.get("items", [])[:3]:  # First 3 items per menu
                    item_count += 1
                    img_count = len(item.get("images", []))
                    print(f"    {item_count}. {item.get('name', 'Unknown')} - {img_count} image(s)")
                    if item.get("images"):
                        print(f"       Image: {item['images'][0][:60]}...")
            
            print(f"{'='*60}\n")
        else:
            print("⚠️  No menus extracted!")
        
        return structured_data
        
    except Exception as e:
        print(f"❌ Error scraping pages: {e}")
        import traceback
        traceback.print_exc()
        return {"menus": []}
    finally:
        # Cleanup temp directory
        try:
            if tmpdir and os.path.exists(tmpdir):
                import shutil
                shutil.rmtree(tmpdir)
        except:
            pass


# if __name__ == '__main__':
#     # Test with McDonald's Pakistan menu
#     test_url = 'https://www.mcdonalds.com.pk/full-menu/'
    
#     print("="*60)
#     print("RESTAURANT MENU SCRAPER")
#     print("="*60)
#     print(f"\nTarget: {test_url}\n")
    
#     result = scrape_pages([test_url])
    
#     # Pretty print results
#     print("\n" + "="*60)
#     print("FINAL JSON OUTPUT:")
#     print("="*60)
#     print(json.dumps(result, indent=2, ensure_ascii=False))
    
#     # Save to file for inspection
#     output_file = 'menu_output.json'
#     with open(output_file, 'w', encoding='utf-8') as f:
#         json.dump(result, f, indent=2, ensure_ascii=False)
#     print(f"\n✓ Full results saved to {output_file}")