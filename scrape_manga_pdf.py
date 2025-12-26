import requests
from bs4 import BeautifulSoup
import os
from PIL import Image
from io import BytesIO
import img2pdf
import re

# Configuration
BASE_URL = "https://blackclover.com.lv/"
OUTPUT_FOLDER = "Black_Clover_Manga"  # Separate folder for PDFs
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# TEST MODE - Set to None to download all chapters
TEST_MODE = None  # Download all chapters

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
            full_url = href if href.startswith('http') else BASE_URL.rstrip('/') + href
            chapter_links.append(full_url)

    # Remove duplicates and sort
    chapter_links = list(set(chapter_links))

    # Sort by chapter number
    def extract_chapter_num(url):
        match = re.search(r'chapter-(\d+)', url)
        return int(match.group(1)) if match else 0

    chapter_links.sort(key=extract_chapter_num)

    print(f"Found {len(chapter_links)} chapters")
    return chapter_links

def get_chapter_images(chapter_url):
    """Get all image URLs from a chapter page"""
    print(f"  Fetching chapter page: {chapter_url}")
    response = requests.get(chapter_url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract chapter title
    title_tag = soup.find('h1')
    chapter_title = title_tag.text.strip() if title_tag else "Unknown Chapter"

    # Find all manga page images
    images = []
    for img in soup.find_all('img'):
        src = img.get('src', '')
        # Look for images from the manga hosting server
        if 'planeptune.us/manga/Black-Clover/' in src:
            images.append(src)

    return chapter_title, images

def download_image_to_memory(img_url):
    """Download image to memory and return PIL Image object"""
    response = requests.get(img_url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BytesIO(response.content)

def create_pdf_from_images(image_urls, output_path, chapter_title):
    """Download images and create a PDF"""
    print(f"  Downloading {len(image_urls)} pages...")

    image_data_list = []

    for idx, img_url in enumerate(image_urls, 1):
        try:
            print(f"    Page {idx}/{len(image_urls)}", end='\r')
            img_data = download_image_to_memory(img_url)
            image_data_list.append(img_data.getvalue())
        except Exception as e:
            print(f"\n    Error downloading page {idx}: {e}")
            continue

    print()  # New line after progress

    if not image_data_list:
        print("  No images downloaded!")
        return False

    # Create PDF from images
    print(f"  Creating PDF with {len(image_data_list)} pages...")
    try:
        with open(output_path, "wb") as f:
            f.write(img2pdf.convert(image_data_list))
        print(f"  [OK] PDF created successfully: {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f"  Error creating PDF: {e}")
        return False

def scrape_manga_to_pdf():
    """Main function to scrape manga and create PDFs"""
    # Create output folder
    output_dir = os.path.join(os.getcwd(), OUTPUT_FOLDER)
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output folder: {output_dir}\n")

    # Get all chapter URLs
    chapter_urls = get_all_chapter_urls()

    if not chapter_urls:
        print("No chapters found!")
        return

    # Limit to test mode if enabled
    if TEST_MODE:
        chapter_urls = chapter_urls[:TEST_MODE]
        print(f"\n*** TEST MODE: Processing only first {TEST_MODE} chapters ***\n")

    # Process each chapter
    success_count = 0
    for idx, chapter_url in enumerate(chapter_urls, 1):
        print(f"\n[{idx}/{len(chapter_urls)}] Processing chapter...")

        try:
            # Get chapter info and image URLs
            chapter_title, image_urls = get_chapter_images(chapter_url)
            print(f"  Title: {chapter_title}")
            print(f"  Pages: {len(image_urls)}")

            if not image_urls:
                print("  No images found, skipping...")
                continue

            # Extract chapter number from URL
            chapter_match = re.search(r'chapter-(\d+)', chapter_url)
            chapter_num = chapter_match.group(1) if chapter_match else str(idx)

            # Create filename using chapter number
            pdf_filename = f"Chapter {chapter_num}.pdf"
            pdf_path = os.path.join(output_dir, pdf_filename)

            # Check if PDF already exists
            if os.path.exists(pdf_path):
                print(f"  Already exists: {pdf_filename}")
                success_count += 1
                continue

            # Create PDF
            if create_pdf_from_images(image_urls, pdf_path, chapter_title):
                success_count += 1

        except Exception as e:
            print(f"  Error processing chapter: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"[DONE] Scraping complete!")
    print(f"[DONE] Successfully created: {success_count}/{len(chapter_urls)} PDFs")
    print(f"[DONE] Saved to: {output_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    print("=" * 60)
    print("Black Clover Manga PDF Scraper")
    print("=" * 60)
    print(f"Working directory: {os.getcwd()}")

    scrape_manga_to_pdf()
