import os
import json

from issue_agents import (
    DomAgent,
    CssAgent,
    JsAgent,
    read_css_files,
    read_js_files,
    chunk_text,
)
from js_corrector_agent import JsCorrectorAgent
from css_corrector_agent import CssCorrectorAgent
from html_audio_video_tool_agent import ExternalToolRecommenderAgent
from html_corrector_agent import HtmlCorrectorAgent
from image_captioning_agent import ImageCaptioningAgent


def analyze_accessibility_issues():
    print("📄 Reading HTML, CSS, and JS files...")

    with open("before/index.html", "r", encoding="utf-8") as f:
        html_code = f.read()

    css_files = read_css_files("before/css")
    css_code = "\n".join(css_files.values())

    js_files = read_js_files("before/js")
    all_js_code = "\n".join(js_files.values())
    js_chunks = chunk_text(all_js_code)

    print("🔍 Running accessibility analysis...")

    dom_agent = DomAgent()
    css_agent = CssAgent()
    js_agent = JsAgent()

    dom_issues = dom_agent.analyze(html_code)
    css_issues = css_agent.analyze(css_code)
    js_issues = []
    for chunk in js_chunks:
        js_issues.extend(js_agent.analyze(chunk))

    print("💾 Saving accessibility issues to JSON files...")

    os.makedirs("outputs/issues", exist_ok=True)
    with open(
        "outputs/issues/accessibility_issues_html.json", "w", encoding="utf-8"
    ) as f:
        json.dump(dom_issues, f, indent=2, ensure_ascii=False)
    with open(
        "outputs/issues/accessibility_issues_css.json", "w", encoding="utf-8"
    ) as f:
        json.dump(css_issues, f, indent=2, ensure_ascii=False)
    with open(
        "outputs/issues/accessibility_issues_js.json", "w", encoding="utf-8"
    ) as f:
        json.dump(js_issues, f, indent=2, ensure_ascii=False)

    print("✅ Accessibility issues saved.")
    return dom_issues, css_issues, js_issues, html_code, css_files, js_files


def generate_image_captions():
    print("📦 Generating external tool tasks from HTML issues...")

    issues_path = "outputs/issues/accessibility_issues_html.json"
    captions = {}

    if os.path.exists(issues_path):
        with open(issues_path, "r", encoding="utf-8") as f:
            issues = json.load(f)

        recommender = ExternalToolRecommenderAgent()
        tool_tasks = recommender.analyze_issues(issues)

        os.makedirs("outputs/tools", exist_ok=True)
        with open("outputs/tools/external_tool_tasks.json", "w", encoding="utf-8") as f:
            json.dump(tool_tasks, f, indent=2)

        print("✅ External tool tasks saved to outputs/tools/external_tool_tasks.json")

        image_filenames = [
            os.path.basename(task["file"])
            for task in tool_tasks
            if task["tool"] == "image_captioning_tool"
        ]

        if image_filenames:
            print("🧠 Running image captioning agent...")
            api_key = "sk-proj-..."  # Replace with your actual API key
            agent = ImageCaptioningAgent(api_key=api_key)
            captions = agent.process_images(image_filenames, image_dir="before/images")

            os.makedirs("outputs/captions", exist_ok=True)
            with open(
                "outputs/captions/image_captions.json", "w", encoding="utf-8"
            ) as f:
                json.dump(captions, f, indent=2, ensure_ascii=False)

            print("✅ Captions saved to outputs/captions/image_captions.json")
        else:
            print("⚠️ No image files found for captioning.")
    else:
        print("⚠️ No HTML issues found for tool recommendation.")

    return captions


def correct_html(dom_issues, html_code, image_captions):
    print("🛠️ Correcting HTML issues...")
    os.makedirs("after", exist_ok=True)
    agent = HtmlCorrectorAgent()
    corrected = agent.analyze_and_correct(
        {"index.html": html_code}, dom_issues, image_captions=image_captions
    )

    with open("after/index.html", "w", encoding="utf-8") as f:
        f.write(corrected["index.html"])
    print("✅ Corrected HTML saved to after/index.html")


def correct_css(css_issues, css_files):
    print("🎨 Correcting CSS issues...")
    os.makedirs("after/css", exist_ok=True)
    agent = CssCorrectorAgent()
    corrected = agent.analyze_and_correct(css_files, css_issues)

    for filename, corrected_code in corrected.items():
        with open(os.path.join("after/css", filename), "w", encoding="utf-8") as f:
            f.write(corrected_code)
    print("✅ Corrected CSS files saved to after/css/")


def correct_js(js_issues, js_files):
    print("🧠 Correcting JS issues...")
    os.makedirs("after/js", exist_ok=True)
    agent = JsCorrectorAgent()
    corrected = agent.analyze_and_correct(js_files, js_issues)

    for filename, corrected_code in corrected.items():
        with open(os.path.join("after/js", filename), "w", encoding="utf-8") as f:
            f.write(corrected_code)
    print("✅ Corrected JS files saved to after/js/")


if __name__ == "__main__":
    dom_issues, css_issues, js_issues, html_code, css_files, js_files = (
        analyze_accessibility_issues()
    )
    image_captions = generate_image_captions()
    correct_html(dom_issues, html_code, image_captions)
    correct_css(css_issues, css_files)
    correct_js(js_issues, js_files)
    print("\n🎉 All steps completed successfully!")
