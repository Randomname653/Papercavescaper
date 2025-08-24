import cloudscraper
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import time
from playwright.async_api import async_playwright, Error as PlaywrightError
import asyncio
from tqdm import tqdm

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'

# --- CONFIGURATION ---
DEFAULT_URL = "https://wallpapercave.com/categories/anime-manga"
DOWNLOAD_DIR = os.path.expanduser("~/Pictures/wallpapers")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
scraper = cloudscraper.create_scraper()

# --- HELPER FUNCTIONS ---
async def scroll_to_bottom(page):
    """Scrolls down the page to trigger lazy-loaded content."""
    print(f"  {Colors.CYAN}> Scrolling page to load all content...{Colors.ENDC}")
    last_height = await page.evaluate("document.body.scrollHeight")
    while True:
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(2000)
        new_height = await page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    print(f"  {Colors.CYAN}> Finished scrolling.{Colors.ENDC}")

def download_image(image_url, download_path):
    """Downloads an image and returns a status string."""
    try:
        if os.path.exists(download_path):
            return "skipped"
        response = scraper.get(image_url, stream=True)
        response.raise_for_status()
        with open(download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        return "downloaded"
    except Exception:
        return "failed"

def get_image_url_from_wallpaper_page(page_url):
    """Gets the direct download link from a wallpaper's specific page."""
    try:
        response = scraper.get(page_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        download_button = soup.find("a", id="tdownload")
        if download_button:
            href = download_button.get("href")
            if href:
                download_link_url = urljoin(page_url, href)
                download_response = scraper.get(download_link_url, allow_redirects=True)
                download_response.raise_for_status()
                return download_response.url
        return None
    except Exception:
        return None

async def fetch_and_download(url, download_dir, semaphore):
    """A wrapper for concurrent downloading, managed by a semaphore."""
    async with semaphore:
        image_url = await asyncio.to_thread(get_image_url_from_wallpaper_page, url)
        if image_url:
            filename = os.path.basename(image_url)
            name, ext = os.path.splitext(filename)
            if not ext:
                filename += ".jpg"
            dl_path = os.path.join(download_dir, filename)
            status = await asyncio.to_thread(download_image, image_url, dl_path)
            return status
    return "failed"

async def main():
    start_time = time.time()
    total_downloaded, total_skipped, total_failed = 0, 0, 0

    print("-" * 50)
    user_input = input(f"Enter a WallpaperCave URL (or press Enter for default):\n> ")
    
    if not user_input:
        target_url = DEFAULT_URL
        print(f"No URL provided. Using default: {Colors.YELLOW}{target_url}{Colors.ENDC}")
    else:
        target_url = user_input.strip().rstrip('/')
        print(f"Using provided URL: {Colors.YELLOW}{target_url}{Colors.ENDC}")
    print("-" * 50)

    if target_url == "https://wallpapercave.com":
        print(f"{Colors.YELLOW}Base URL detected. Please provide a more specific URL.{Colors.ENDC}")
        # ... instruction print statements ...
    elif "/categories/" in target_url:
        album_urls = await process_category(target_url)
        print(f"\nStarting automatic download process for {len(album_urls)} albums...")
        for index, album_url in enumerate(album_urls):
            d, s, f = await process_album(album_url, index, len(album_urls))
            total_downloaded += d
            total_skipped += s
            total_failed += f
    elif "/w/wp" in target_url:
        print(f"\n{Colors.CYAN}--- SINGLE IMAGE MODE ---{Colors.ENDC}")
        image_url = get_image_url_from_wallpaper_page(target_url)
        if image_url:
            dl_path = os.path.join(DOWNLOAD_DIR, os.path.basename(image_url))
            status = download_image(image_url, dl_path)
            if status == "downloaded":
                total_downloaded += 1
    else:
        d, s, f = await process_album(target_url, 0, 1)
        total_downloaded += d
        total_skipped += s
        total_failed += f

    end_time = time.time()
    total_seconds = end_time - start_time
    minutes, seconds = divmod(total_seconds, 60)
    manual_time_seconds = total_downloaded * 5
    time_saved_seconds = manual_time_seconds - total_seconds

    print("\n" + "="*50)
    print(f"{Colors.GREEN}Scraping Complete!{Colors.ENDC}")
    print(f"  - Downloaded: {Colors.GREEN}{total_downloaded}{Colors.ENDC}")
    print(f"  - Skipped (already exist): {Colors.YELLOW}{total_skipped}{Colors.ENDC}")
    print(f"  - Failed: {Colors.RED}{total_failed}{Colors.ENDC}")
    print(f"  - Total run time: {Colors.CYAN}{int(minutes)} minutes and {seconds:.2f} seconds{Colors.ENDC}")
    if time_saved_seconds > 0:
        saved_minutes, saved_seconds = divmod(time_saved_seconds, 60)
        print(f"  - Time saved (vs. 5s/image): {Colors.CYAN}{int(saved_minutes)} minutes and {saved_seconds:.2f} seconds{Colors.ENDC}")
    print("="*50)

async def process_category(category_url):
    print(f"\n{Colors.CYAN}--- DISCOVERY MODE: Finding albums... ---{Colors.ENDC}")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(**p.devices['Desktop Chrome'])
        page = await context.new_page()
        await page.goto(category_url, timeout=90000)
        await page.wait_for_load_state('networkidle', timeout=60000)
        await scroll_to_bottom(page)
        album_locators = page.locator("a.albumthumbnail")
        album_count = await album_locators.count()
        album_urls = []
        for i in range(album_count):
            href = await album_locators.nth(i).get_attribute("href")
            if href:
                album_urls.append(urljoin(category_url, href))
        await browser.close()
        return album_urls

async def process_album(album_url, index, total):
    downloaded, skipped, failed = 0, 0, 0
    print(f"\n[{index + 1}/{total}] Processing Album: {Colors.YELLOW}{album_url}{Colors.ENDC}")
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(**p.devices['Desktop Chrome'])
        page = await context.new_page()
        try:
            await page.goto(album_url, timeout=90000)
            await scroll_to_bottom(page)
            wallpaper_locators = page.locator("a.albumthumbnail, div.album-image > a, a.wpinkw")
            wallpaper_count = await wallpaper_locators.count()
            print(f"  Found {wallpaper_count} individual wallpapers.")
            if wallpaper_count > 0:
                urls_to_process = []
                for i in range(wallpaper_count):
                    href = await wallpaper_locators.nth(i).get_attribute("href")
                    if href:
                        urls_to_process.append(urljoin(album_url, href))
                
                semaphore = asyncio.Semaphore(5)
                tasks = [fetch_and_download(url, DOWNLOAD_DIR, semaphore) for url in urls_to_process]
                
                with tqdm(total=len(tasks), desc="  Downloading", unit=" wallpaper") as progress_bar:
                    for future in asyncio.as_completed(tasks):
                        status = await future
                        if status == "downloaded":
                            downloaded += 1
                        elif status == "skipped":
                            skipped += 1
                        else:
                            failed += 1
                        progress_bar.update(1)
        except PlaywrightError as e:
            print(f"  {Colors.RED}--> Skipping album due to a browser error: {e} <--{Colors.ENDC}")
        finally:
            if browser.is_connected():
                await browser.close()
    print(f"  Album stats: {Colors.GREEN}{downloaded} downloaded{Colors.ENDC}, {Colors.YELLOW}{skipped} skipped{Colors.ENDC}, {Colors.RED}{failed} failed{Colors.ENDC}.")
    return downloaded, skipped, failed

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Script interrupted by user. Exiting.{Colors.ENDC}")
    except Exception as e:
        print(f"\n{Colors.RED}A critical error occurred: {e}{Colors.ENDC}")
    finally:
        print(f"\n{Colors.CYAN}Process finished.{Colors.ENDC}")
