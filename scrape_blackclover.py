import requests
from bs4 import BeautifulSoup
import os
import json
import time
from urllib.parse import urljoin

# Configuration
BASE_URL = "https://blackclover.com.lv/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_all_chapter_urls():
    """Fetch all chapter URLs from the main page"""
    print("Fetching chapter list...")
    response = requests.get(BASE_URL, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all chapter links
    chapter_links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if '/manga/black-clover-chapter-' in href:
            chapter_links.append(href)

    # Remove duplicates and sort
    chapter_links = list(set(chapter_links))
    chapter_links.sort()

    print(f"Found {len(chapter_links)} chapters")
    return chapter_links

def get_chapter_info(chapter_url):
    """Get images and metadata from a single chapter"""
    print(f"Fetching: {chapter_url}")
    response = requests.get(chapter_url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract chapter title
    title_tag = soup.find('h1')
    chapter_title = title_tag.text.strip() if title_tag else "Unknown"

    # Find all manga page images
    images = []
    for img in soup.find_all('img'):
        src = img.get('src', '')
        if 'planeptune.us/manga/Black-Clover/' in src or 'black-clover' in src.lower():
            images.append(src)

    return {
        'url': chapter_url,
        'title': chapter_title,
        'images': images
    }

def download_image(img_url, save_path):
    """Download a single image"""
    try:
        response = requests.get(img_url, headers=HEADERS, timeout=30)
        response.raise_for_status()

        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  Error downloading {img_url}: {e}")
        return False

def scrape_all_manga():
    """Main scraping function"""
    # Get all chapter URLs
    chapter_urls = get_all_chapter_urls()

    if not chapter_urls:
        print("No chapters found!")
        return

    # Store metadata
    all_metadata = []

    # Process each chapter
    for idx, chapter_url in enumerate(chapter_urls, 1):
        print(f"\n[{idx}/{len(chapter_urls)}] Processing chapter...")

        try:
            chapter_info = get_chapter_info(chapter_url)
            all_metadata.append(chapter_info)

            print(f"  Title: {chapter_info['title']}")
            print(f"  Images found: {len(chapter_info['images'])}")

            # Download each image
            for img_idx, img_url in enumerate(chapter_info['images'], 1):
                # Extract filename from URL
                filename = os.path.basename(img_url.split('?')[0])

                # If filename is not descriptive, create one
                if not filename or len(filename) < 5:
                    filename = f"chapter_{idx}_page_{img_idx}.png"

                save_path = os.path.join(os.getcwd(), filename)

                # Skip if already downloaded
                if os.path.exists(save_path):
                    print(f"  [{img_idx}/{len(chapter_info['images'])}] Already exists: {filename}")
                    continue

                print(f"  [{img_idx}/{len(chapter_info['images'])}] Downloading: {filename}")
                download_image(img_url, save_path)

                # Small delay to avoid overwhelming the server
                time.sleep(0.5)

            # Delay between chapters
            time.sleep(1)

        except Exception as e:
            print(f"  Error processing chapter: {e}")
            continue

    # Save metadata to JSON file
    metadata_file = os.path.join(os.getcwd(), 'manga_metadata.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(all_metadata, indent=2, fp=f, ensure_ascii=False)

    print(f"\n✓ Scraping complete!")
    print(f"✓ Metadata saved to: manga_metadata.json")
    print(f"✓ Total chapters processed: {len(all_metadata)}")

if __name__ == "__main__":
    print("Black Clover Manga Scraper")
    print("=" * 50)
    print(f"Working directory: {os.getcwd()}")
    print("=" * 50)

    scrape_all_manga()
