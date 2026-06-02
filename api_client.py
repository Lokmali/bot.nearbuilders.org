import os
import httpx
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("NEARBUILDERS_API_URL", "https://nearbuilders.org/api/builders/v1/builders")


async def submit_builder(payload: dict) -> tuple[bool, str]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(API_URL, json=payload)
            if response.status_code in (200, 201):
                return True, "Success"
            else:
                return False, f"API returned {response.status_code}: {response.text}"
        except httpx.RequestError as e:
            return False, f"Request error: {e}"
