import base64
from PIL import Image
from io import BytesIO
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables for OpenAI API key
load_dotenv()


class ImageCaptioningAgent:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_alt_text(self, image_path: str) -> str:
        try:
            with Image.open(image_path) as image:
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_bytes = buffered.getvalue()
                img_base64 = base64.b64encode(img_bytes).decode("utf-8")

            result = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant that generates concise and descriptive alt text for web accessibility.",
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{img_base64}"
                                },
                            },
                            {
                                "type": "text",
                                "text": "Describe this image in one sentence as alt text.",
                            },
                        ],
                    },
                ],
            )
            return result.choices[0].message.content.strip()

        except Exception as e:
            return f"[Error generating alt text: {str(e)}]"

    def process_images(
        self, image_filenames: list[str], image_dir: str = "before/images"
    ) -> dict[str, str]:
        result = {}
        for filename in image_filenames:
            full_path = os.path.join(image_dir, filename)
            print(f"🔎 Processing: {full_path}")
            caption = self.generate_alt_text(full_path)
            result[filename] = caption
        return result
