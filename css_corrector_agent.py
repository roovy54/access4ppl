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


class CssCorrectorAgent(BaseAgent):
    def build_prompt(self, css_code: str, issues: list[str]) -> str:
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        return (
            "You are an expert web accessibility and CSS developer.\n"
            "Given the following accessibility issues found in CSS files and the CSS code, "
            "provide corrected CSS code for each file to fix the issues.\n"
            "Return the result as a Python dictionary mapping each CSS filename to its corrected CSS code as a string.\n"
            "Make sure to keep the code formatting clean and do not change unrelated code.\n\n"
            f"Accessibility Issues:\n{issues_text}\n\n"
            f"CSS Code:\n{css_code}\n\n"
            "Provide only the Python dictionary as output."
        )

    def analyze_and_correct(
        self, css_files: dict[str, str], issues: list[str]
    ) -> dict[str, str]:
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

        # Strip ```python fences if present
        if response_text.startswith("```python"):
            response_text = response_text[len("```python") :].strip()
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()

        try:
            corrected_dict = eval(response_text, {"__builtins__": None}, {})
            if isinstance(corrected_dict, dict):
                return {k: str(v) for k, v in corrected_dict.items()}
            else:
                print("Warning: Corrector response is not a dictionary")
                return {}
        except Exception as e:
            print(f"Error parsing corrector response: {e}")
            return {}


if __name__ == "__main__":
    css_dir = "before/css"
    issues_path = "accessibility_issues_css.json"
    output_dir = "after/css"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load accessibility issues from file
    with open(issues_path, "r", encoding="utf-8") as f:
        issues = json.load(f)

    # Read all CSS files from the before/css directory
    css_files = {}
    for filename in os.listdir(css_dir):
        if filename.endswith(".css"):
            filepath = os.path.join(css_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                css_files[filename] = f.read()

    # Run correction
    agent = CssCorrectorAgent()
    corrected = agent.analyze_and_correct(css_files, issues)

    # Save corrected CSS code into after/css/ directory
    for filename, corrected_code in corrected.items():
        out_path = os.path.join(output_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(corrected_code)

    print(f"Corrected CSS files written to: {output_dir}")
