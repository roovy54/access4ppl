import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BaseAgent:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def call_llm(self, messages: list) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return ""


class HtmlCorrectorAgent(BaseAgent):
    def build_prompt(
        self,
        html_code: str,
        issues: list[str],
        image_captions: dict[str, str] = {},
    ) -> str:
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        captions_text = (
            "\n".join(
                f"{fname}: {caption}" for fname, caption in image_captions.items()
            )
            if image_captions
            else "None"
        )

        return (
            "You are an expert web developer specialized in accessibility.\n\n"
            "Your job is to fix **only** the HTML-based accessibility issues listed below.\n"
            "These issues are related to structure, missing attributes, or semantic markup.\n\n"
            "**Guidelines:**\n"
            "- Do NOT fix issues requiring audio/video transcripts.\n"
            "- Do NOT change any CSS or JavaScript logic.\n"
            "- Use provided image captions to add descriptive `alt` text where `<img>` is missing it.\n"
            "- Keep the structure and styling intact unless needed for fixing the issue.\n"
            "- Do NOT introduce extra explanations. Just return the corrected HTML code.\n\n"
            f"Issues:\n{issues_text}\n\n"
            f"Image Captions:\n{captions_text}\n\n"
            f"HTML Code:\n{html_code}\n"
        )

    def analyze_and_correct(
        self,
        html_files: dict[str, str],
        issues: list[str],
        image_captions: dict[str, str] = {},
    ) -> dict[str, str]:
        filename = "index.html"
        html_code = html_files.get(filename, "")
        prompt = self.build_prompt(html_code, issues, image_captions)

        messages = [
            {
                "role": "system",
                "content": "You are an expert in accessible HTML coding.",
            },
            {"role": "user", "content": prompt},
        ]

        response_text = self.call_llm(messages)

        # Remove code block fences if present
        if response_text.startswith("```html"):
            response_text = response_text[len("```html") :].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()

        return {filename: response_text}


if __name__ == "__main__":
    html_dir = "before"
    output_dir = "after"
    issues_path = os.path.join(html_dir, "accessibility_issues_html.json")
    html_path = os.path.join(html_dir, "index.html")

    os.makedirs(output_dir, exist_ok=True)

    # Load accessibility issues
    with open(issues_path, "r", encoding="utf-8") as f:
        issues = json.load(f)

    # Load HTML file
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()

    # Optional: Load image captions if available
    image_captions = {}  # You can populate this dict with {filename: caption}

    # Run correction
    agent = HtmlCorrectorAgent()
    corrected_html = agent.analyze_and_correct(
        {"index.html": html_code}, issues, image_captions
    )

    # Save corrected file
    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(corrected_html["index.html"])

    print(f"✅ Corrected HTML written to: {output_path}")
