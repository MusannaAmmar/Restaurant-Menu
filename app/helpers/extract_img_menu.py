import json
from openai import OpenAI
import os
from app.base_models.menu import MenusSchema
import base64


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Function to encode the image
# @time_function('encode_image')
async def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


# @time_function('extract_img_menu')
async def extract_img_menu(file_path):
    print(f"Extracting menu from image: {file_path}")
    base64_image = await encode_image(file_path)
    response = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "Extract restaurant menu info and output valid JSON matching this schema: "
                f"{MenusSchema.model_json_schema()}"},
            {
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Extract restaurant menu info and output valid JSON matching this schema: "
                    f"{MenusSchema.model_json_schema()}"},
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                },
            ],
        }],
        text_format=MenusSchema
    )

    data = response.output_parsed.model_dump()

    return data


# # print(extract_img_menu(r"C:\Users\buzz\Desktop\download.jpg"))



