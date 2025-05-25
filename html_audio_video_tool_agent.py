import os
import json
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv

# Load API key
load_dotenv()


class BaseAgent:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def call_llm(self, messages: List[Dict[str, str]]) -> str:
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


class ExternalToolRecommenderAgent(BaseAgent):
    def build_prompt(self, issues: List[str]) -> str:
        issue_text = "\n".join(f"- {issue}" for issue in issues)
        return (
            "You are an expert accessibility engineer.\n"
            "You are given a list of accessibility issues detected in HTML, CSS, or JavaScript files.\n"
            "Your job is to recommend which external tools should be used based on the issues.\n\n"
            "Supported tools:\n"
            "- 'image_captioning_tool': Use if image alt attributes are missing or non-descriptive.\n"
            "- 'video_transcription_tool': Use if video elements are missing captions.\n"
            "- Other tools may be included if you can justify them based on accessibility needs.\n\n"
            "Return your answer strictly as a Python dictionary in this format:\n"
            "{\n"
            "  'image_captioning_tool': ['img1.jpg', 'img2.png'],\n"
            "  'video_transcription_tool': ['video1.mp4']\n"
            "}\n"
            "Use only the file name or relative path from the issue description if available.\n"
            "If the file is not specified, write 'UNKNOWN'.\n\n"
            f"Accessibility Issues:\n{issue_text}\n"
        )

    def recommend_tools(self, issues: List[str]) -> Dict[str, List[str]]:
        prompt = self.build_prompt(issues)
        messages = [
            {"role": "system", "content": "You are an expert accessibility engineer."},
            {"role": "user", "content": prompt},
        ]
        response_text = self.call_llm(messages)

        # Clean up ```python fences if present
        if response_text.startswith("```python"):
            response_text = response_text[len("```python") :].strip()
        if response_text.endswith("```"):
            response_text = response_text[:-3].strip()

        try:
            result = eval(response_text, {"__builtins__": None}, {})
            if isinstance(result, dict):
                return {tool: list(map(str, files)) for tool, files in result.items()}
            else:
                print("⚠️ Output is not a dictionary.")
                return {}
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            return {}


if __name__ == "__main__":
    issues_path = "accessibility_issues_html.json"
    output_path = "external_tool_tasks.json"

    if not os.path.exists(issues_path):
        raise FileNotFoundError(f"{issues_path} not found.")

    with open(issues_path, "r", encoding="utf-8") as f:
        issues = json.load(f)

    agent = ExternalToolRecommenderAgent()
    result = agent.recommend_tools(issues)

    print(json.dumps(result, indent=2))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"✅ External tool recommendations saved to: {output_path}")
