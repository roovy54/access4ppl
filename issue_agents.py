import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class BaseAgent:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    def analyze(self, code_snippet: str) -> list[str]:
        prompt = self.build_prompt(code_snippet)
        messages = [
            {
                "role": "system",
                "content": "You are an expert in web accessibility.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]
        response_text = self.call_llm(messages)

        # Strip ```python and closing ``` fences if present exactly like that
        if response_text.startswith("```python"):
            response_text = response_text[len("```python") :].strip()
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()

        # Try to safely parse the response text as Python list
        try:
            issues_list = eval(response_text, {"__builtins__": None}, {})
            if isinstance(issues_list, list):
                return [str(issue) for issue in issues_list]
            else:
                print("Warning: LLM response is not a list")
                return [response_text]
        except Exception as e:
            print(f"Error parsing LLM response as list: {e}")
            return [response_text]

    def build_prompt(self, code_snippet: str) -> str:
        raise NotImplementedError

    def call_llm(self, messages: list) -> str:
        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return ""


class DomAgent(BaseAgent):
    def build_prompt(self, code_snippet: str) -> str:
        return (
            "Analyze the following HTML code for accessibility issues. "
            "Return a Python list of strings, each describing one accessibility issue in detail so that another system can understand and fix it easily. "
            "Do NOT include severity levels, just a clear, concise description of the issue and the affected HTML element.\n\n"
            f"{code_snippet}\n\n"
            "Example output format:\n"
            "['Image element <img> missing alt text.', 'Heading levels are skipped or improperly nested.']"
        )


class CssAgent(BaseAgent):
    def build_prompt(self, code_snippet: str) -> str:
        return (
            "Analyze the following CSS code for accessibility issues related to:\n"
            "- Insufficient color contrast between text and background\n"
            "- Using color alone to convey information\n"
            "- Missing visible focus indicators on interactive elements\n"
            "- Fixed font sizes that prevent resizing\n"
            "- Overlapping or hidden content caused by positioning or z-index\n"
            "- Animations or flashing that can trigger seizures\n"
            "- Poor responsive design affecting usability\n"
            "Return a Python list of strings, each describing one accessibility issue clearly and fully for easy understanding and future fixing. "
            "Do NOT include severity levels.\n\n"
            f"{code_snippet}\n\n"
            "Example output format:\n"
            "['Text color #ccc on white background has insufficient contrast.', 'Focus outline removed from buttons making keyboard navigation hard.']"
        )


class JsAgent(BaseAgent):
    def build_prompt(self, code_snippet: str) -> str:
        return (
            "Analyze the following JavaScript code for accessibility issues such as:\n"
            "- Dynamic content updates without ARIA live region announcements\n"
            "- Custom controls missing keyboard support\n"
            "- Improper focus management (focus not moved or trapped incorrectly)\n"
            "- Event handlers that only respond to mouse events\n"
            "- Missing or incorrect ARIA roles on interactive elements\n"
            "- Use of alert(), confirm(), prompt() dialogs that disrupt accessibility\n"
            "- Content changes not announced to assistive technologies\n"
            "- Tab order issues due to dynamic element manipulation\n"
            "Return a Python list of strings, each describing one issue clearly and fully for easy understanding and fixing. "
            "Do NOT include severity levels.\n\n"
            f"{code_snippet}\n\n"
            "Example output format:\n"
            "['Modal dialog does not move focus to itself when opened.', 'Custom dropdown does not support keyboard navigation.']"
        )


def chunk_text(text: str, max_tokens: int = 1500) -> list[str]:
    lines = text.split("\n")
    chunks = []
    current_chunk = []
    token_estimate = 0

    for line in lines:
        token_estimate += len(line.split())  # crude token estimation
        current_chunk.append(line)
        if token_estimate > max_tokens:
            chunks.append("\n".join(current_chunk))
            current_chunk = []
            token_estimate = 0

    if current_chunk:
        chunks.append("\n".join(current_chunk))

    return chunks


def read_css_files(css_dir: str) -> dict[str, str]:
    css_files = {}
    for root, _, files in os.walk(css_dir):
        for file in files:
            if file.endswith(".css"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    css_files[file] = f.read()
    return css_files


def read_js_files(js_dir: str) -> dict[str, str]:
    js_files = {}
    for root, _, files in os.walk(js_dir):
        for file in files:
            if file.endswith(".js"):
                path = os.path.join(root, file)
                with open(path, "r", encoding="utf-8") as f:
                    js_files[file] = f.read()
    return js_files


if __name__ == "__main__":
    # Read HTML file
    with open("before/index.html", "r", encoding="utf-8") as f:
        html_code = f.read()

    # Read all CSS files
    css_files = read_css_files("before/css")
    css_code = "\n".join(css_files.values())

    # Read all JS files
    js_files = read_js_files("before/js")
    all_js_code = "\n".join(js_files.values())
    js_chunks = chunk_text(all_js_code)

    # Initialize agents
    dom_agent = DomAgent()
    css_agent = CssAgent()
    js_agent = JsAgent()

    # Analyze code snippets and get lists of issues
    dom_issues = dom_agent.analyze(html_code)
    css_issues = css_agent.analyze(css_code)
    js_issues = []
    for chunk in js_chunks:
        js_issues.extend(js_agent.analyze(chunk))

    # Now dom_issues, css_issues, js_issues are all python lists of strings
    # You can process or save them as needed

    # For demo, print nicely
    # print("--- DOM Accessibility Issues ---")
    # for issue in dom_issues:
    #     print(f"- {issue}")

    # print("\n--- CSS Accessibility Issues ---")
    # for issue in css_issues:
    #     print(f"- {issue}")

    # print("\n--- JS Accessibility Issues ---")
    # for issue in js_issues:
    #     print(f"- {issue}")

    # Save issues as JSON files
    with open("accessibility_issues_html.json", "w", encoding="utf-8") as f:
        json.dump(dom_issues, f, indent=2, ensure_ascii=False)

    with open("accessibility_issues_css.json", "w", encoding="utf-8") as f:
        json.dump(css_issues, f, indent=2, ensure_ascii=False)

    with open("accessibility_issues_js.json", "w", encoding="utf-8") as f:
        json.dump(js_issues, f, indent=2, ensure_ascii=False)

    print("Accessibility issues saved to JSON files in 'before/' folder.")
