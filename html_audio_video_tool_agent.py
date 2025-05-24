import re
import json
import os
from typing import List, Dict


class ExternalToolRecommenderAgent:
    def __init__(self):
        pass

    def analyze_issues(self, issues: List[str]) -> List[Dict[str, str]]:
        tool_usage = []

        for issue in issues:
            # Check for missing alt or non-descriptive alt attributes on images
            img_match = re.search(r"<img>.*?src '([^']+)'", issue)
            if img_match:
                file_path = img_match.group(1)
                if (
                    "missing an alt attribute" in issue.lower()
                    or "non-descriptive alt" in issue.lower()
                ):
                    tool_usage.append(
                        {"tool": "image_captioning_tool", "file": file_path}
                    )

            # Check for missing captions in videos
            video_match = re.search(r"<video>", issue)
            if video_match and "captions" in issue.lower():
                tool_usage.append(
                    {
                        "tool": "video_transcription_tool",
                        "file": "UNKNOWN",  # update if video file name is present in your HTML scan
                    }
                )

        return tool_usage


# Example usage
if __name__ == "__main__":
    issues_path = "accessibility_issues_html.json"

    # Load issues from JSON file
    if os.path.exists(issues_path):
        with open(issues_path, "r", encoding="utf-8") as f:
            issues = json.load(f)
    else:
        raise FileNotFoundError(f"{issues_path} not found.")

    agent = ExternalToolRecommenderAgent()
    result = agent.analyze_issues(issues)

    print(json.dumps(result, indent=2))

    # Optionally save to a file
    with open("external_tool_tasks.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
