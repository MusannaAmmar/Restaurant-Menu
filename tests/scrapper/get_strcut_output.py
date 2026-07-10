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

with open('tests/scrapper/sample.txt', 'r') as f:
    text = f.read()

response = client.responses.parse(
    model="gpt-4o-2024-08-06",
    input=[
        {"role": "system", "content": "Extract restaurant menu info and output valid JSON matching this schema: "
            f"{MenuItemSchema.model_json_schema()}"},
        {
            "role": "user",
            "content": text,
        },
    ],
    text_format=MenuListSchema,
)

print(response.output_parsed.model_dump())