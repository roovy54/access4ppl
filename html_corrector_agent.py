import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables for OpenAI API key
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
        self, html_code: str, issues: list[str], image_captions: dict[str, str]
    ) -> str:
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        captions_text = "\n".join(
            f"{filename}: {caption}" for filename, caption in image_captions.items()
        )

        return (
            "You are an expert web developer specialized in accessibility.\n"
            "Below are HTML accessibility issues and the HTML code. Your job is to fix only those issues "
            "that can be addressed by editing HTML structure or attributes (e.g., adding labels, ARIA roles, skip links, lang tags).\n"
            "Use the image captions provided to add meaningful alt text to <img> tags when appropriate.\n"
            "DO NOT attempt to fix issues requiring video transcripts — ignore them.\n"
            "Return only the corrected HTML string.\n\n"
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
            {
                "role": "user",
                "content": prompt,
            },
        ]

        response_text = self.call_llm(messages)

        # Remove ```html fences if present
        if response_text.startswith("```html"):
            response_text = response_text[len("```html") :].strip()
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()

        return {filename: response_text}


if __name__ == "__main__":
    html_dir = "before"
    issues_path = "accessibility_issues_html.json"
    output_dir = "after"

    os.makedirs(output_dir, exist_ok=True)

    # Read issues
    with open(issues_path, "r", encoding="utf-8") as f:
        issues = json.load(f)

    # Read only index.html
    html_path = os.path.join(html_dir, "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html_code = f.read()

    # Correct
    agent = HtmlCorrectorAgent()
    corrected = agent.analyze_and_correct({"index.html": html_code}, issues)

    # Save corrected HTML
    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(corrected["index.html"])

    print(f"Corrected HTML written to: {output_path}")
