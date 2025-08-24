<div align="center">

# 🖼️ WallpaperCave Scraper

**A high-performance Python tool to download entire wallpaper albums from WallpaperCave.com.**

![Python](https://img.shields.io/badge/python-3.11+-blue.svg)

</div>

This script was built to be a robust and flexible solution for scraping wallpapers, capable of handling modern web features like dynamic content and lazy loading.

---

## ✨ Core Features

* **Multi-Mode Operation**: Intelligently handles different types of URLs, including broad categories, specific albums, and even single wallpaper pages.
* **Fully Automated**: Discovers all albums within a category and downloads from each one in a single run.
* **High-Performance**: Downloads up to 5 images concurrently, dramatically speeding up the process.
* **User-Friendly**: Provides an interactive prompt for the URL, a live progress bar for downloads, and detailed final statistics.
* **Robust & Resilient**: Built with Playwright to handle JavaScript-heavy pages and includes error handling to skip broken albums without crashing.

---

## ⚙️ Setup

Follow these steps to set up the scraper.

**1. Clone or Download**

First, get the project files onto your local machine.

**2. Create a Virtual Environment**

It's highly recommended to use a virtual environment to keep dependencies clean.

```bash
python -m venv venv
```
Activate it:
* On Windows:
    ```bash
    .\venv\Scripts\activate
    ```
* On macOS/Linux:
    ```bash
    source venv/bin/activate
    ```

**3. Install Dependencies**

Install all the required Python libraries from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

**4. Install Browser Files**

Playwright needs to download the browser instances it will control. This is a one-time setup.

```bash
playwright install
```

---

## 🚀 How to Use

Simply run the script from your terminal:

```bash
python wallpaper_scraper.py
```

The script will launch and prompt you to enter a URL from `WallpaperCave.com`.

* **To scrape a whole category**, provide a category URL (e.g., `https://wallpapercave.com/categories/games`).
* **To scrape a single album**, provide an album URL (e.g., `https://wallpapercave.com/the-witcher-3-wild-hunt-wallpapers`).
* **For the default option**, just press `Enter`, and it will use the pre-configured URL.
