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
            print(f"❌ Error calling OpenAI API: {e}")
            return ""


class CssCorrectorAgent(BaseAgent):
    def build_prompt(self, css_code: str, issues: list[str]) -> str:
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        return (
            "You are an expert web developer specializing in CSS accessibility.\n\n"
            "You will be given:\n"
            "- A list of CSS accessibility issues.\n"
            "- CSS code from one or more files (with filename markers).\n\n"
            "**Your task:**\n"
            "- Fix the accessibility issues *only* in the CSS.\n"
            "- Keep unrelated styles unchanged.\n"
            "- Return your answer strictly as a Python dictionary mapping each filename to its corrected CSS code.\n"
            "- Do NOT return explanations, just the dictionary object.\n\n"
            f"Accessibility Issues:\n{issues_text}\n\n"
            f"CSS Code:\n{css_code}\n"
        )

    def analyze_and_correct(
        self, css_files: dict[str, str], issues: list[str]
    ) -> dict[str, str]:
        # Combine all CSS code with file markers
        combined_code = "\n\n".join(
            f"/* FILE: {filename} */\n{code}" for filename, code in css_files.items()
        )

        prompt = self.build_prompt(combined_code, issues)

        messages = [
            {
                "role": "system",
                "content": "You are an expert in web accessibility and CSS.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        response_text = self.call_llm(messages)

        # Remove ```python fences if present
        if response_text.startswith("```python"):
            response_text = response_text[len("```python") :].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()

        try:
            # Safely evaluate the dictionary (no builtins for security)
            corrected_dict = eval(response_text, {"__builtins__": None}, {})
            if isinstance(corrected_dict, dict):
                return {k: str(v) for k, v in corrected_dict.items()}
            else:
                print("⚠️ Warning: Response is not a dictionary.")
                return {}
        except Exception as e:
            print(f"❌ Error parsing response as dictionary: {e}")
            return {}


if __name__ == "__main__":
    css_dir = "before/css"
    output_dir = "after/css"
    issues_path = os.path.join("before", "accessibility_issues_css.json")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load accessibility issues
    with open(issues_path, "r", encoding="utf-8") as f:
        issues = json.load(f)

    # Read all CSS files from input directory
    css_files = {}
    for filename in os.listdir(css_dir):
        if filename.endswith(".css"):
            filepath = os.path.join(css_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                css_files[filename] = f.read()

    # Run correction
    agent = CssCorrectorAgent()
    corrected_css = agent.analyze_and_correct(css_files, issues)

    # Save corrected files
    for filename, code in corrected_css.items():
        output_path = os.path.join(output_dir, filename)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code)

    print(f"✅ Corrected CSS files written to: {output_dir}")
