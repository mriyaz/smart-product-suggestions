# Import necessary libraries
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import json
import os
from typing import List, Dict, Optional, Union
import logging
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import urllib.parse
import io
import PyPDF2
from bs4 import BeautifulSoup
import requests
from utils import parse_with_chatgpt

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define Scraper class


class Scraper:
    def __init__(self):
        # Initialize session and webdriver
        self.session = requests.Session()
        # Set up Chrome options (headless, etc.)
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--disable-dev-shm-usage")
        service = Service('C:\\Windows\\chromedriver-win64\\chromedriver.exe')
        # Create Chrome webdriver instance
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def __del__(self):
        # Quit the webdriver if it exists
        if hasattr(self, 'driver'):
            self.driver.quit()

    def handle_popup(self):
        # Try to find and close any popups on the page
        try:
            WebDriverWait(self.driver, 5).until(EC.presence_of_element_located(
                (By.CSS_SELECTOR,
                 "button[class*='close'], div[class*='popup'] button, div[id*='popup'] button")
            ))

            close_button = self.driver.find_element(
                By.CSS_SELECTOR, "button[class*='close'], div[class*='popup'] button, div[id*='popup'] button")
            close_button.click()

            # Log success
            logger.info("Popup closed successfully.")
        except (TimeoutException, NoSuchElementException):
            # Log failure
            logger.info("No popup found or unable to close popup.")

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        pdf_file = io.BytesIO(pdf_content)

        # Use PyPDF2 to extract text from PDF content
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # Return extracted text as string
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text

    def extract_text_from_html(self, html: str) -> str:
        # Use BeautifulSoup to extract text from HTML
        soup = BeautifulSoup(html, 'html.parser')

        # Return extracted text as string
        return soup.get_text(separator='\n', strip=True)

    def standardize_menu(self, raw_menu: Dict) -> Dict:
        # Convert raw menu dict to standardized format
        standardized_menu = {"sections": []}

        # Handle potential errors in raw_menu
        if "error" in raw_menu:
            return raw_menu

        # Return standardized menu dict
        for section in raw_menu.get("sections", []):
            std_section = {
                "name": section.get("section_name", "Uncategorized"),
                "items": []
            }

            for item in section.get("items", []):
                if isinstance(item, dict):
                    std_item = {
                        "name": item.get("name", ""),
                        "description": item.get("description", "")
                    }
                    std_section["items"].append(std_item)
            if std_section["items"]:
                standardized_menu["sections"].append(std_section)

        return standardized_menu

    def scrape_menu(self, url: str) -> Dict:
        # Implement retry logic (max 3 attempts)
        max_retries = 3
        # For each attempt:
        for attempt in range(max_retries):
            try:
                # If URL is PDF, use requests to get content and extract text
                if url.lower().endswith('.pdf'):
                    response = self.session.get(url)
                    response.raise_for_status()
                    text = self.extract_text_from_pdf(response.content)
                else:
                    # Else, use Selenium to load page and extract HTML
                    self.driver.get(url)
                    # Handle popups
                    self.handle_popup()

                    # Wait for the menu element to be present
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, "body"))
                    )

                    # Scroll to load dynamic content
                    self.driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(5)  # Increased wait time for content to load

                    # Extract text from HTML
                    html = self.driver.page_source
                    text = self.extract_text_from_html(html)

                prompt = f"""
                Parse the following menu text and extract menu items (dishes or products) with their descriptions (if available). 
                Must format the output as a valid JSON object with the following structure:
                {{
                    "sections": [
                        {{
                            "section_name": "Section Name",
                            "items": [
                                {{
                                    "name": "Item Name",
                                    "description": "Item Description"
                                }}
                            ]
                        }}
                    ]
                }}

                Instructions:

                1.Extract all menu sections and the items(dishes or products)  within eacg menu section.
                2.For each item (dish or product), capture the name (dish name or product name) and description (ingredients). If any field is missing, return an empty string ("").
                3.Only return the structured JSON output, no additional text.
                Here is the menu text to parse:
                {text} 
                """

                content = "You are a helpful assistant that parses restaurant menus and returns the information in a valid JSON format."
                # Use parse_with_chatgpt() to parse the text
                raw_menu = parse_with_chatgpt(prompt, content)

                # Standardize and return the standardized menu
                return self.standardize_menu(raw_menu)
            except Exception as e:
                # If all attempts fail, return error dict
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1} failed. Retrying...")
                    time.sleep(5)
                else:
                    logger.error(f"Error scraping {url}: {e}")
                    return {"error": f"Failed to scrape menu: {str(e)}"}

    def scrape_venue_menus(self, venues: List[Dict[str, str]]) -> Dict[str, Dict]:
        # Initialize empty dict for all menus
        all_menus = {}
        # For each venue in venues:
        for venue in venues:
            name = venue['name']
            url = venue['website']
            # Log start of scraping for venue
            logger.info(f"Scraping menu for {name}...")
            # Try to scrape menu for venue
            try:
                menu = self.scrape_menu(url)
                # If successful, add to all_menus dict
                all_menus[name] = menu

            except Exception as e:
                # If failed, log error and add error message to all_menus
                logger.error(f"Failed to scrape menu for {name}: {e}")
                # all_menus[name] = {"error": f"Failed to scrape menu: {str(e)}"}

            # Wait 5 seconds before next venue
            time.sleep(5)
        # Return all_menus dict
        return all_menus


# Define helper functions
def load_venues(filename: str) -> List[Dict[str, str]]:
    # Open and read JSON file
    with open(filename, 'r') as f:
        # Return list of venue dictionaries
        return json.load(f)


def load_existing_menus(filename: str) -> Dict[str, Dict]:
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_menus_to_file(menus: Dict[str, Dict], filename: str):
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    # Open file for writing/appending
    with open(filename, 'a', encoding='utf-8') as f:
        # Write menus dict as formatted JSON
        json.dump(menus, f, indent=2, ensure_ascii=False)

    # Main execution


if __name__ == "__main__":
    # Load venues from data/venues.json
    venues = load_venues("../data/venues_with_menu_urls.json")

    # Load existing menus
    existing_menus = load_existing_menus("../data/menus.json")

    # Create Scraper instance
    scraper = Scraper()

    menus = existing_menus.copy()

    for venue in venues:
        name = venue['name']
        url = venue['website']
        if name not in menus:
            logger.info(f"Scraping menu for {name}...")
            try:
                menu = scraper.scrape_menu(url)
                menus[name] = menu

                logger.info(f"Menu for {name} scraped successfully.")
            except Exception as e:
                logger.error(f"Failed to scrape menu for {name}: {e}")
                # menus[name] = {"error": f"Failed to scrape menu: {str(e)}"}
            time.sleep(5)  # Add a delay between requests to avoid overloading
        else:
            logger.info(f"Menu for {name} already exists, skipping.")

    # Save after each successful scrape
    save_menus_to_file(menus, "../data/menus.json")

    # Print confirmation message
    print(f"Menus saved to data/menus.json")
