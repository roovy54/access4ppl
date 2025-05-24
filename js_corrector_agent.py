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


class JsCorrectorAgent(BaseAgent):
    def build_prompt(self, js_code: str, issues: list[str]) -> str:
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        return (
            "You are an expert web accessibility and JavaScript developer.\n"
            "Given the following accessibility issues found in JavaScript files and the JS code, "
            "provide corrected JavaScript code for each file to fix the issues.\n"
            "Return the result as a Python dictionary mapping each JS filename to its corrected JS code as a string.\n"
            "Make sure to keep the code formatting clean and do not change unrelated code.\n\n"
            f"Accessibility Issues:\n{issues_text}\n\n"
            f"JavaScript Code:\n{js_code}\n\n"
            "Provide only the Python dictionary as output."
        )

    def analyze_and_correct(
        self, js_files: dict[str, str], issues: list[str]
    ) -> dict[str, str]:
        combined_code = "\n\n".join(
            f"// FILE: {filename}\n{code}" for filename, code in js_files.items()
        )
        prompt = self.build_prompt(combined_code, issues)

        messages = [
            {
                "role": "system",
                "content": "You are an expert in web accessibility and JavaScript.",
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
    js_dir = "before/js"
    issues_path = "accessibility_issues_js.json"
    output_dir = "after/js"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load accessibility issues from file
    with open(issues_path, "r", encoding="utf-8") as f:
        issues = json.load(f)

    # Read all JS files from the before/js directory, skipping ones starting with 'ajax'
    js_files = {}
    for filename in os.listdir(js_dir):
        if filename.endswith(".js") and not filename.startswith("ajax"):
            filepath = os.path.join(js_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                js_files[filename] = f.read()

    # Run correction
    agent = JsCorrectorAgent()
    corrected = agent.analyze_and_correct(js_files, issues)

    # Save corrected JS code into after/js/ directory
    for filename, corrected_code in corrected.items():
        out_path = os.path.join(output_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(corrected_code)

    print(f"Corrected JS files written to: {output_dir}")
