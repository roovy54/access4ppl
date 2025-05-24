import requests
import subprocess
import json
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def fetch_page(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text


def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup


def extract_resources(soup, base_url):
    # Get all linked CSS files
    css_links = [
        urljoin(base_url, link["href"])
        for link in soup.find_all("link", rel="stylesheet")
        if link.get("href")
    ]

    # Get all JS files
    js_links = [
        urljoin(base_url, script["src"])
        for script in soup.find_all("script")
        if script.get("src")
    ]

    return css_links, js_links


def download_files(urls):
    files_content = {}
    for url in urls:
        try:
            r = requests.get(url)
            r.raise_for_status()
            files_content[url] = r.text
        except Exception as e:
            print(f"Failed to download {url}: {e}")
    return files_content


def get_js_ast(js_code):
    temp_file = "temp.js"
    with open("temp.js", "w", encoding="utf-8") as f:
        f.write(js_code)
    result = subprocess.run(
        ["node", "parse_js_ast.js", "temp.js"],
        capture_output=True,
        text=True,
        check=True,
    )
    os.remove(temp_file)
    return json.loads(result.stdout)


def get_css_ast(css_code):
    temp_file = "temp.css"
    with open("temp.css", "w", encoding="utf-8") as f:
        f.write(css_code)
    result = subprocess.run(
        ["node", "parse_css_ast.js", "temp.css"],
        capture_output=True,
        text=True,
        check=True,
    )
    os.remove(temp_file)
    return json.loads(result.stdout)


def process_website_assets(url):
    """
    Given a webpage URL, fetch and parse the HTML, CSS, and JS content.
    Returns:
        - soup: Parsed DOM object using BeautifulSoup
        - css_asts: Dictionary mapping CSS URLs to their parsed ASTs
        - js_asts: Dictionary mapping JS URLs to their parsed ASTs
    """
    # Step 1: Fetch HTML
    html = fetch_page(url)

    # Step 2: Parse HTML to DOM
    soup = parse_html(html)

    # Step 3: Extract CSS and JS links
    css_urls, js_urls = extract_resources(soup, url)

    # Step 4: Download CSS and JS files
    css_files = download_files(css_urls)
    js_files = download_files(js_urls)

    # Step 5: Parse CSS files to AST
    css_asts = {}
    for url, code in css_files.items():
        try:
            css_asts[url] = get_css_ast(code)
        except Exception as e:
            print(f"Failed to parse CSS AST for {url}: {e}")

    # Step 6: Parse JS files to AST
    js_asts = {}
    for url, code in js_files.items():
        try:
            js_asts[url] = get_js_ast(code)
        except Exception as e:
            print(f"Failed to parse JS AST for {url}: {e}")

    return soup, css_asts, js_asts, css_files, js_files
