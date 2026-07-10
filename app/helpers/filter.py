import json
from openai import OpenAI
from pydantic import BaseModel
from typing import List
import os

from dotenv import load_dotenv

load_dotenv()


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class UrlListSchema(BaseModel):
    urls: List[str]



async def filter_menu_related_urls(urls):
    response = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": """You are a URL filtering expert specializing in restaurant websites. "
            "Your task is to analyze a list of URLs and return only those that are likely to contain restaurant menu information."
            "\n\nInclude URLs that might contain:\n- Menu pages (/menu, /food, /dining, /restaurant-menu)\n- "
            "Restaurant pages with menu sections\n- Food and beverage listings\n- Online ordering pages\n- "
            "Restaurant information pages that typically include menu details\n- PDF menu links\n-"
            " Gallery pages with food images"
            "\n\nExclude URLs that are clearly:\n- Contact pages\n- Location/directions pages\n- "
            "About us pages\n- Social media links\n- Blog posts (unless food-related)\n- "
            "Reservation pages\n- Career/job pages\n- Privacy policy/terms pages\n- General website navigation"
            "\n\nReturn a clean list of URLs that are most likely to contain menu-related content."
            "\n\nSchema: " + f"{UrlListSchema.model_json_schema()}"""},
            {
                "role": "user",
                "content": json.dumps(urls),
            },
        ],
        text_format=UrlListSchema,
    )
    return response.output_parsed.urls



# if __name__=='__main__':
#     url=filter_menu_related_urls(['https://www.mcdonalds.com.pk/','https://www.mcdonalds.com.pk/full-menu/','https://www.mcdonalds.com.pk/careers/'])
#     print(url)