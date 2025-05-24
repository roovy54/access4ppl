import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re


def safe_filename(url):
    """Create a filesystem-safe filename from a URL."""
    parsed = urlparse(url)
    path = parsed.netloc + parsed.path
    if path.endswith("/"):
        path += "index"
    filename = re.sub(r"[^\w\-_.]", "_", path)
    return filename


def save_text_file(folder, filename, content):
    filepath = os.path.join(folder, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved: {filepath}")


def save_binary_file(folder, filename, content):
    filepath = os.path.join(folder, filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)
    print(f"Saved: {filepath}")


def fetch_url(url):
    print(f"Downloading: {url}")
    resp = requests.get(url)
    resp.raise_for_status()
    return resp


def fetch_page(url):
    resp = fetch_url(url)
    return resp.text


def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup


def extract_resources(soup, base_url):
    css_links = [
        urljoin(base_url, link["href"])
        for link in soup.find_all("link", rel="stylesheet")
        if link.get("href")
    ]

    js_links = [
        urljoin(base_url, script["src"])
        for script in soup.find_all("script")
        if script.get("src")
    ]

    inline_css = [style.string for style in soup.find_all("style") if style.string]

    inline_js = [
        script.string
        for script in soup.find_all("script")
        if not script.get("src") and script.string
    ]

    img_links = [
        urljoin(base_url, img["src"]) for img in soup.find_all("img") if img.get("src")
    ]

    # Extract video URLs from <video> and nested <source> tags
    video_links = set()
    for video_tag in soup.find_all("video"):
        src = video_tag.get("src")
        if src:
            video_links.add(urljoin(base_url, src))
        for source in video_tag.find_all("source"):
            src = source.get("src")
            if src:
                video_links.add(urljoin(base_url, src))

    return css_links, js_links, inline_css, inline_js, img_links, list(video_links)


def download_files(urls, folder, binary=False):
    files_content = {}
    for url in urls:
        try:
            resp = fetch_url(url)
            content = resp.content if binary else resp.text
            filename = safe_filename(url)
            ext = os.path.splitext(filename)[1].lower()

            # Add extension if missing for text files
            if not ext and not binary:
                ext = ".txt"
                filename += ext
            elif binary and not ext:
                ext = ".bin"
                filename += ext

            save_func = save_binary_file if binary else save_text_file
            save_func(folder, filename, content)

            files_content[url] = filename
        except Exception as e:
            print(f"Failed to download {url}: {e}")
    return files_content


def save_inline_files(contents, folder, prefix, extension):
    filenames = []
    for i, content in enumerate(contents, 1):
        filename = f"{prefix}_inline_{i}.{extension}"
        save_text_file(folder, filename, content)
        filenames.append(filename)
    return filenames


def rewrite_asset_links(
    soup,
    css_files,
    js_files,
    img_files,
    video_files,
    base_url,
    css_folder="css",
    js_folder="js",
    img_folder="images",
    video_folder="videos",
):
    # Rewrite CSS href links
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href")
        if href:
            abs_url = urljoin(base_url, href)
            if abs_url in css_files:
                link["href"] = os.path.join(css_folder, css_files[abs_url]).replace(
                    "\\", "/"
                )

    # Rewrite JS src links
    for script in soup.find_all("script"):
        src = script.get("src")
        if src:
            abs_url = urljoin(base_url, src)
            if abs_url in js_files:
                script["src"] = os.path.join(js_folder, js_files[abs_url]).replace(
                    "\\", "/"
                )

    # Rewrite image src links
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            abs_url = urljoin(base_url, src)
            if abs_url in img_files:
                img["src"] = os.path.join(img_folder, img_files[abs_url]).replace(
                    "\\", "/"
                )

    # Rewrite video src and nested <source> src links
    for video_tag in soup.find_all("video"):
        src = video_tag.get("src")
        if src:
            abs_url = urljoin(base_url, src)
            if abs_url in video_files:
                video_tag["src"] = os.path.join(
                    video_folder, video_files[abs_url]
                ).replace("\\", "/")
        for source in video_tag.find_all("source"):
            src = source.get("src")
            if src:
                abs_url = urljoin(base_url, src)
                if abs_url in video_files:
                    source["src"] = os.path.join(
                        video_folder, video_files[abs_url]
                    ).replace("\\", "/")


def save_main_html(soup, folder, filename="index.html"):
    html_content = str(soup.prettify())
    save_text_file(folder, filename, html_content)


def process_website_assets(url, output_folder="website_download"):
    os.makedirs(output_folder, exist_ok=True)

    # Step 1: Fetch HTML
    html = fetch_page(url)

    # Step 2: Parse HTML to DOM
    soup = parse_html(html)

    # Step 3: Extract resources (now includes videos)
    css_urls, js_urls, inline_css, inline_js, img_urls, video_urls = extract_resources(
        soup, url
    )

    print(
        f"Found {len(css_urls)} CSS files, {len(js_urls)} JS files, "
        f"{len(inline_css)} inline CSS blocks, {len(inline_js)} inline JS blocks, "
        f"{len(img_urls)} images, and {len(video_urls)} videos."
    )

    # Step 4: Download resources and save locally
    css_folder = os.path.join(output_folder, "css")
    js_folder = os.path.join(output_folder, "js")
    img_folder = os.path.join(output_folder, "images")
    video_folder = os.path.join(output_folder, "videos")

    css_files = download_files(css_urls, css_folder, binary=False)
    js_files = download_files(js_urls, js_folder, binary=False)
    img_files = download_files(img_urls, img_folder, binary=True)
    video_files = download_files(
        video_urls, video_folder, binary=True
    )  # videos are binary

    # Step 5: Save inline CSS and JS files (optional)
    save_inline_files(inline_css, css_folder, "style", "css")
    save_inline_files(inline_js, js_folder, "script", "js")

    # Step 6: Rewrite asset URLs inside HTML to point locally
    rewrite_asset_links(
        soup,
        css_files,
        js_files,
        img_files,
        video_files,
        url,
        css_folder="css",
        js_folder="js",
        img_folder="images",
        video_folder="videos",
    )

    # Step 7: Save modified HTML locally
    save_main_html(soup, output_folder)

    print("Download complete.")

    return {
        "html_file": os.path.join(output_folder, "index.html"),
        "css_files": css_files,
        "js_files": js_files,
        "image_files": img_files,
        "video_files": video_files,
        "inline_css_count": len(inline_css),
        "inline_js_count": len(inline_js),
    }


if __name__ == "__main__":
    url = "https://www.washington.edu/accesscomputing/AU/before.html#"
    output_dir = "before"
    process_website_assets(url, output_dir)
