import json
import os
import logging
import time
from typing import List, Dict, Union
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
import PyPDF2
import io
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils import parse_with_chatgpt, save_json, load_json

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='ingredient_retrieval.log',
                    filemode='w')
logger = logging.getLogger(__name__)


class Scraper:
    def __init__(self):
        self.session = requests.Session()
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service('C:\\Windows\\chromedriver-win64\\chromedriver.exe')
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.existing_ingredients = self.load_existing_ingredients()

    def load_existing_ingredients(self) -> Dict[str, str]:
        """Load existing ingredients from the JSON file."""
        filename = "../data/ingredients.json"
        if os.path.exists(filename):
            data = load_json(filename)
            return {item['name']: item['ingredients'] for item in data}
        return {}

    def __del__(self):
        if hasattr(self, 'driver'):
            self.driver.quit()

    def handle_popup(self):
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "button[class*='close'], div[class*='popup'] button, div[id*='popup'] button")
            ))
            close_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[class*='close'], div[class*='popup'] button, div[id*='popup'] button")
            close_button.click()
            logger.info("Popup closed successfully.")
        except (TimeoutException, NoSuchElementException):
            logger.info("No popup found or unable to close popup.")

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except PyPDF2.PdfReadError as e:
            logger.error(f"Error reading PDF: {e}")
            return ""
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def extract_text_from_html(self, html: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text(separator='\n', strip=True)

    def find_pdf_links(self, html: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html, 'html.parser')
        pdf_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.lower().endswith('.pdf'):
                full_url = urljoin(base_url, href)
                pdf_links.append(full_url)
        return pdf_links

    def extract_ingredients(self, text: str) -> List[str]:
        prompt = f"""
        Extract all unique ingredients from the provided restaurant menu text. 
        Return them as a comma-separated list, without duplicates. 
        If no ingredients are found, return an empty string.
        Provide only the list of ingredients, with no additional text.
        Menu Text:
        {text}
        """

        content = "You are a helpful assistant that extracts ingredients from restaurant menu text."

        message = [
            {"role": "system", "content": content},
            {"role": "user", "content": prompt}
        ]

        try:
            content = parse_with_chatgpt(message)
            # Extract ingredients directly
            ingredients = [ingredient.strip()
                           for ingredient in content.split(',') if ingredient.strip()]
            logger.info(f"Raw ingredients response: {ingredients}")
            return ingredients
        except Exception as e:
            logger.error(f"Error extracting ingredients: {e}")
            return []

    def scrape_pdf(self, url: str) -> List[str]:
        try:
            response = self.session.get(url)
            response.raise_for_status()
            text = self.extract_text_from_pdf(response.content)
            return self.extract_ingredients(text)
        except Exception as e:
            logger.error(f"Error scraping PDF {url}: {e}")
            return []

    def scrape_menu(self, url: str) -> List[str]:
        max_retries = 3
        all_ingredients = set()

        for attempt in range(max_retries):
            try:
                self.driver.get(url)
                self.handle_popup()
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
                )
                self.driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(5)
                html = self.driver.page_source

                # Extract ingredients from HTML
                text = self.extract_text_from_html(html)
                html_ingredients = set(self.extract_ingredients(text))
                all_ingredients.update(html_ingredients)

                # Find and scrape PDF links
                pdf_links = self.find_pdf_links(html, url)
                for pdf_link in pdf_links:
                    pdf_ingredients = set(self.scrape_pdf(pdf_link))
                    all_ingredients.update(pdf_ingredients)

                return list(all_ingredients)
            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1} failed. Retrying...")
                    time.sleep(5)
                else:
                    logger.error(f"Error scraping {url}: {e}")
                    return list(all_ingredients)

    def scrape_venue_ingredients(self, venues: List[Dict[str, str]]) -> List[Dict[str, str]]:
        new_ingredients = []
        for venue in venues:
            name = venue['name']
            url = venue['website']
            if name in self.existing_ingredients:
                logger.info(
                    f"Skipping {name} as it already exists in ingredients.json")
                continue

            logger.info(f"Scraping ingredients for {name}...")
            try:
                ingredients = self.scrape_menu(url)
                if ingredients:
                    new_ingredients.append({
                        "name": name,
                        "ingredients": ", ".join(ingredients)
                    })
                    self.existing_ingredients[name] = ", ".join(
                        ingredients)  # Update existing_ingredients
                    logger.info(
                        f"Ingredients extracted for {name}: {ingredients}")
                else:
                    logger.warning(f"No ingredients found for {name}")
            except Exception as e:
                logger.error(f"Failed to scrape ingredients for {name}: {e}")
            time.sleep(5)
        return new_ingredients


def load_venues(filename: str) -> List[Dict[str, str]]:
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading venues from {filename}: {e}")
        return []


def save_ingredients_to_file(new_ingredients: List[Dict[str, str]], filename: str):
    try:
        # Load existing data
        existing_data = load_json(filename) if os.path.exists(filename) else []

        # Create a set of existing restaurant names
        existing_names = {item['name'] for item in existing_data}

        # Append new ingredients
        for item in new_ingredients:
            if item['name'] not in existing_names:
                existing_data.append(item)
                existing_names.add(item['name'])

        # Save merged data
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Ingredients saved to {filename}")
    except Exception as e:
        logger.error(f"Error saving ingredients to {filename}: {e}")


if __name__ == "__main__":
    venues = load_venues("../data/venues_with_menu_urls.json")
    if not venues:
        logger.error("No venues loaded. Exiting.")
        exit(1)

    scraper = Scraper()
    new_ingredients = scraper.scrape_venue_ingredients(venues)
    save_ingredients_to_file(new_ingredients, "../data/ingredients.json")
    print(f"New ingredients saved to ../data/ingredients.json")
