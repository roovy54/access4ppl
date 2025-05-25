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
            print(f"❌ Error calling OpenAI API: {e}")
            return ""


class JsCorrectorAgent(BaseAgent):
    def build_prompt(self, js_code: str, issues: list[str]) -> str:
        issues_text = "\n".join(f"- {issue}" for issue in issues)
        return (
            "You are an expert web accessibility and JavaScript developer.\n\n"
            "You will be given:\n"
            "- A list of accessibility issues found in JavaScript files.\n"
            "- JavaScript code from one or more files (each marked with its filename).\n\n"
            "**Your task:**\n"
            "- Fix the issues in the JS code.\n"
            "- Do not modify unrelated logic.\n"
            "- Return your answer strictly as a Python dictionary mapping each JS filename to its corrected JS code.\n"
            "- Do NOT include explanations, just the dictionary.\n\n"
            f"Accessibility Issues:\n{issues_text}\n\n"
            f"JavaScript Code:\n{js_code}\n"
        )

    def analyze_and_correct(
        self, js_files: dict[str, str], issues: list[str]
    ) -> dict[str, str]:
        # Merge JS files with comment headers
        combined_code = "\n\n".join(
            f"// FILE: {filename}\n{code}" for filename, code in js_files.items()
        )
        prompt = self.build_prompt(combined_code, issues)

        messages = [
            {
                "role": "system",
                "content": "You are an expert in web accessibility and JavaScript.",
            },
            {"role": "user", "content": prompt},
        ]

        response_text = self.call_llm(messages)

        # Remove ```python code fences if present
        if response_text.startswith("```python"):
            response_text = response_text[len("```python") :].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()

        try:
            corrected_dict = eval(response_text, {"__builtins__": None}, {})
            if isinstance(corrected_dict, dict):
                return {k: str(v) for k, v in corrected_dict.items()}
            else:
                print("⚠️ Warning: Response is not a valid dictionary.")
                return {}
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return {}


if __name__ == "__main__":
    js_dir = "before/js"
    issues_path = os.path.join("before", "accessibility_issues_js.json")
    output_dir = "after/js"

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load list of accessibility issues
    with open(issues_path, "r", encoding="utf-8") as f:
        issues = json.load(f)

    # Read all JS files except ones starting with 'ajax'
    js_files = {}
    for filename in os.listdir(js_dir):
        if filename.endswith(".js") and not filename.startswith("ajax"):
            filepath = os.path.join(js_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                js_files[filename] = f.read()

    # Run JS correction
    agent = JsCorrectorAgent()
    corrected_js = agent.analyze_and_correct(js_files, issues)

    # Save corrected JS files
    for filename, corrected_code in corrected_js.items():
        out_path = os.path.join(output_dir, filename)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(corrected_code)

    print(f"✅ Corrected JS files written to: {output_dir}")
