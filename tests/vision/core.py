import json
from openai import OpenAI
from pydantic import BaseModel, RootModel
from typing import List

client = OpenAI(api_key="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")

class MenuItemSchema(BaseModel):
    name: str
    description: str | None = None
    price: float | None = None

class MenuListSchema(BaseModel):
    items: List[MenuItemSchema]

response = client.responses.parse(
    model="gpt-4.1-mini",
    input=[
        {"role": "system", "content": "Extract restaurant menu info and output valid JSON matching this schema: "
            f"{MenuItemSchema.model_json_schema()}"},
        {
        "role": "user",
        "content": [
            {"type": "input_text", "text": "what's in this image?"},
            {
                "type": "input_image",
                "image_url": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR-THsP_HAKXhkkdzZZxXEaNQlzGMm73qkjrg&s",
            },
        ],
    }],
    text_format=MenuListSchema
)

print(response.output_parsed.model_dump())