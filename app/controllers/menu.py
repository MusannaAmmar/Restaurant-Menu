
import asyncio
import os
import uuid
import httpx
from fastapi import APIRouter, UploadFile, File, Request,Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List,Optional
from app.helpers.scrapper import scrape_pages
from app.helpers.extract_img_menu import extract_img_menu
from app.helpers.extract_item_names import extract_food_item_names
from app.helpers.generate_3d_image import generate_flux_kontext_image
import time
import json
import tempfile
import shutil


router = APIRouter()

class URLsProcessRequest(BaseModel):
    urls: List[str]=None
    # image:Optional[str]=None

# @time_function('')
async def download_image(image_url: str) -> str:
    """Download image from URL and save locally, return the local path"""
    try:
        cache_dir = "uploads/temp_images"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}.png"
        local_path = os.path.join(cache_dir, unique_filename)
        
        # Download image
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url, follow_redirects=True, timeout=30.0)
            response.raise_for_status()
            
        with open(local_path, "wb") as f:
            f.write(response.content)
        
        print(f"Downloaded image to: {local_path}")
        return local_path
        
    except Exception as e:
        print(f"Error downloading image from {image_url}: {str(e)}")
        raise


async def generate_3d_images_for_items(data: dict) -> dict:
    """Generate 3D images for all menu items - either from images or item names"""
    if not isinstance(data, dict) or "menus" not in data:
        return data
    
    try:
        for menu in data.get("menus", []):
            for section in menu.get("sections", []):
                for item in section.get("items", []):
                    item_name = item.get("name", "Food item")
                    existing_images = item.get("images", [])
                    
                    generated_images = []
                    
                    # Case 1: Item has existing images
                    if existing_images and len(existing_images) > 0:
                        for image_url in existing_images:
                            local_image_path = None
                            try:
                                print(f"Processing image for '{item_name}' from {image_url}")
                                
                                # Download image to local path
                                local_image_path = await download_image(image_url)
                                
                                output = generate_flux_kontext_image(
                                    prompt=f"""Look at this image of '{item_name}'. 
Now create a completely new, realistic 3D rendered image of '{item_name}' using your own imagination and creativity.
Do NOT replicate or copy anything from the input image. 
Instead, generate a high-quality 3D visualization of '{item_name}' that looks like it was rendered in a 3D studio.
Style: Clean white background, professional studio lighting, high detail, realistic shading, smooth edges, no text, no watermarks, no hands, no extra props.""",
                                    input_path=local_image_path,
                                    aspect_ratio="1:1",
                                    output_format="jpg",
                                    safety_tolerance=2,
                                    api_token=os.environ.get("REPLICATE_API_TOKEN"),
                                )
                                
                                # Handle list or string response from Replicate
                                image_url_result = str(output[0]) if isinstance(output, list) and output else str(output)
                                generated_images.append(image_url_result)
                                print(f"Generated 3D image for '{item_name}': {image_url_result}")
                                
                            except Exception as e:
                                print(f"Error generating 3D image for '{item_name}' from image: {str(e)}")
                            
                            finally:
                                # Clean up downloaded image
                                if local_image_path and os.path.exists(local_image_path):
                                    try:
                                        os.remove(local_image_path)
                                    except Exception as cleanup_error:
                                        print(f"Warning: Could not delete temporary image {local_image_path}: {cleanup_error}")
                    
                    # Case 2: No images, generate based on item name
                    else:
                        try:
                            print(f"Generating 3D image for '{item_name}' based on item name only")
                            
                            output = generate_flux_kontext_image(
                                prompt=f"""Generate a realistic and appetizing 3D rendered image of '{item_name}'.
Create a professional, high-quality 3D visualization as if it was rendered in a 3D studio.
Style: Clean white background, professional studio lighting, high detail, realistic shading, smooth edges, mouth-watering appeal, no text, no watermarks, no hands, no extra props.
Make it look delicious and professional suitable for a restaurant menu.""",
                                # input_path=local_image_path,
                                aspect_ratio="1:1",
                                output_format="jpg",
                                safety_tolerance=2,
                                api_token=os.environ.get("REPLICATE_API_TOKEN"),
                            )
                            
                            # Handle list or string response from Replicate
                            image_url_result = str(output[0]) if isinstance(output, list) and output else str(output)
                            generated_images.append(image_url_result)
                            print(f"Generated 3D image for '{item_name}' from name: {image_url_result}")
                            
                        except Exception as e:
                            print(f"Error generating 3D image for '{item_name}' from name: {str(e)}")
                    
                    # Update item with generated images
                    item["images"] = generated_images if generated_images else []
        
        return data
        
    except Exception as e:
        print(f"Error in generate_3d_images_for_items: {str(e)}")
        return data

@router.post("/process-urls", tags=["menu"])
async def process_urls(
    request: URLsProcessRequest
):
    try:        
        data = await scrape_pages(request.urls)
        
        # Generate 3D images for all menu items
        data = await generate_3d_images_for_items(data)
        
        return JSONResponse(
            content={
                "status": True,
                "msg": f"URLs received and processing in background",
                "data": {
                    "urls_count": len(request.urls),
                    "data": data,
                    "urls": request.urls
                }
            },
            status_code=202
        )
        
    except Exception as e:
        return JSONResponse(
            content={
                "status": False,
                "msg": f"Error processing URLs: {str(e)}",
                "data": None
            },
            status_code=500
        )

@router.post("/upload-image", tags=["menu"])
async def upload_image_file(
    request: Request,
    image: UploadFile = File(..., description="Upload an image file")
):
    try:
        upload_dir = "uploads/images"
        os.makedirs(upload_dir, exist_ok=True)

        if not image.content_type.startswith("image/"):
            return JSONResponse(
                content={
                    "status": False,
                    "msg": f"File {image.filename} is not a valid image",
                    "data": None
                },
                status_code=400
            )

        file_extension = os.path.splitext(image.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        with open(file_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        data = await extract_img_menu(file_path)
        item_names = await extract_food_item_names(data)

        # Generate 3D images for all extracted items
        data = await generate_3d_images_for_items(data)
        # Delete the uploaded image file after processing
        try:
            os.remove(file_path)
        except Exception as delete_error:
            print(f"Warning: Could not delete file {file_path}: {delete_error}")

        return JSONResponse(
            content={
                "status": True,
                "msg": "Image received and processing in background",
                "data": {
                    "uploaded_image": item_names,
                    "data": data
                }
            },
            status_code=202
        )

    except Exception as e:
        return JSONResponse(
            content={
                "status": False,
                "msg": f"Error during image upload: {str(e)}",
                "data": None
            },
            status_code=500
        )


async def process_urls_in_background(urls):
    """Background task to scrape URLs and generate 3D images."""
    try:
        data = await scrape_pages(urls)
        data = await generate_3d_images_for_items(data)
        print(f"[Background] URL processing completed")
    except Exception as e:
        print(f"[Background] Error in process_urls_in_background: {e}")

async def process_images_in_background(file_path):
    """Background task to extract images and generate 3D images."""
    try:
        img_data = await extract_img_menu(file_path)
        item_names = await extract_food_item_names(img_data)
        data = await generate_3d_images_for_items(img_data)
        print(f"[Background] Image processing completed")
    except Exception as e:
        print(f"[Background] Error in process_images_in_background: {e}")


@router.post("/prepare-menu", tags=["menu"])
async def prepare_menu(
    urls_json: Optional[str] = Form(None),
    image: UploadFile = File(None)
):
    try:
        urls = None
        if urls_json:
            data = json.loads(urls_json)
            urls = data.get("urls")

        if not urls and not image:
            return JSONResponse(
                content={"status": False, "msg": "Either URL or image is required", "data": None},
                status_code=400
            )

        # 🔹 Process URLs asynchronously
        if urls:
            urls_results=asyncio.create_task(process_urls_in_background(urls))
            print('URL Results',urls_results)
        # 🔹 Save uploaded image temporarily and pass its path
        if image:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as tmp:
                shutil.copyfileobj(image.file, tmp)
                tmp_path = tmp.name

            # pass the file path, not UploadFile
            image_results=asyncio.create_task(process_images_in_background(tmp_path))
            print('Image Results',image_results)
        return JSONResponse(
            content={"status": True, "msg": "Your menu is preparing, kindly wait 5 minutes", "data": None},
            status_code=200
        )

    except Exception as e:
        return JSONResponse(
            content={"status": False, "msg": f"Error: {str(e)}", "data": None},
            status_code=500
        )
