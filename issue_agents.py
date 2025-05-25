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

        # Strip ```python and closing ``` if present
        if response_text.startswith("```python"):
            response_text = response_text[len("```python") :].strip()
            if response_text.endswith("```"):
                response_text = response_text[:-3].strip()

        # Safely parse the list
        try:
            issues_list = eval(response_text, {"__builtins__": None}, {})
            if isinstance(issues_list, list):
                return [str(issue) for issue in issues_list]
            else:
                print("Warning: LLM response is not a list")
                return [response_text]
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
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
            "Analyze the following HTML code for **any and all** accessibility issues. "
            "Be exhaustive and check for:\n"
            "- Missing alt attributes on <img>\n"
            "- Improper heading structure or skipped heading levels\n"
            "- Non-semantic tags used instead of semantic ones\n"
            "- Missing form labels or misassociated labels\n"
            "- Inaccessible link text (e.g., 'click here')\n"
            "- Visual-only cues\n"
            "- Missing ARIA roles on landmarks\n"
            "- Non-keyboard focusable elements\n"
            "- Missing `lang` attribute or incorrect usage\n"
            "- Tables missing headers or structure\n\n"
            "Return only a **Python list of strings**, each one describing a unique accessibility issue and the element involved.\n\n"
            f"{code_snippet}\n\n"
            "Example:\n['Image element <img> missing alt text.', 'Heading levels are skipped or improperly nested.']"
        )


class CssAgent(BaseAgent):
    def build_prompt(self, code_snippet: str) -> str:
        return (
            "Analyze the following CSS code for accessibility issues. Be thorough and check for:\n"
            "- Insufficient contrast between text and background\n"
            "- Use of color alone to convey information\n"
            "- Hidden or removed focus indicators\n"
            "- Fixed or absolute font sizes\n"
            "- Content overlapping or hidden due to positioning/z-index\n"
            "- Animations/flashing violating accessibility\n"
            "- Lack of responsive design\n"
            "- Use of background images for critical text\n\n"
            "Return only a **Python list of strings**, each one describing an issue clearly and mentioning the CSS rule or selector involved.\n\n"
            f"{code_snippet}\n\n"
            "Example:\n['Text color #ccc on white background has insufficient contrast.', 'Focus outline removed from buttons.']"
        )


class JsAgent(BaseAgent):
    def build_prompt(self, code_snippet: str) -> str:
        return (
            "Analyze the following JavaScript code for accessibility issues. Look for:\n"
            "- Dynamic DOM updates without ARIA live region announcements\n"
            "- Custom UI components lacking keyboard interaction\n"
            "- Incorrect or missing focus management\n"
            "- Mouse-only event listeners (e.g., click without keydown)\n"
            "- Use of alert()/confirm() disrupting screen readers\n"
            "- Incomplete ARIA roles/attributes\n"
            "- Dynamic tab order issues\n"
            "- Time-based or animated content that lacks user control\n\n"
            "Return only a **Python list of strings**, each clearly describing a single accessibility issue and the JS behavior or element involved.\n\n"
            f"{code_snippet}\n\n"
            "Example:\n['Custom dropdown lacks keyboard navigation.', 'Modal does not trap focus when opened.']"
        )


def chunk_text(text: str, max_tokens: int = 1500) -> list[str]:
    lines = text.split("\n")
    chunks = []
    current_chunk = []
    token_estimate = 0

    for line in lines:
        token_estimate += len(line.split())  # crude token estimate
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

    # Analyze code
    dom_issues = dom_agent.analyze(html_code)
    css_issues = css_agent.analyze(css_code)
    js_issues = []
    for chunk in js_chunks:
        js_issues.extend(js_agent.analyze(chunk))

    # Save output
    with open("before/accessibility_issues_html.json", "w", encoding="utf-8") as f:
        json.dump(dom_issues, f, indent=2, ensure_ascii=False)

    with open("before/accessibility_issues_css.json", "w", encoding="utf-8") as f:
        json.dump(css_issues, f, indent=2, ensure_ascii=False)

    with open("before/accessibility_issues_js.json", "w", encoding="utf-8") as f:
        json.dump(js_issues, f, indent=2, ensure_ascii=False)

    print("✅ Accessibility issues saved to JSON files in 'before/' folder.")
