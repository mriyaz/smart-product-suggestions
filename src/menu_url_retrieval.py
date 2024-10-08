import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_selenium():
    # Set up Selenium WebDriver with headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)

def find_menu_link(url, driver):
    try:
        # Navigate to the URL
        driver.get(url)
        # Wait for the body tag to be present
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        # Define common menu-related keywords
        menu_keywords = ['menu', 'food', 'drink', 'dining', 'eat', 'cuisine']
        
        # Search for links containing these keywords
        for keyword in menu_keywords:
            elements = driver.find_elements(By.XPATH, f"//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{keyword}')]")
            if elements:
                # Return the first matching link
                return elements[0].get_attribute('href')

        # If no menu link found, return the original URL
        return url
    except Exception as e:
        # Log any errors and return the original URL
        logger.error(f"Error finding menu link for {url}: {e}")
        return url

def load_processed_venues(file_path):
    # Load already processed venues from a JSON file
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning(f"Error reading {file_path}. File might be empty or contain invalid JSON. Starting with an empty list.")
    return []

def save_processed_venue(venue, file_path):
    # Load existing processed venues
    processed_venues = load_processed_venues(file_path)
    
    # Check if the venue already exists in the list
    existing_venue = next((v for v in processed_venues if v['name'] == venue['name']), None)
    if existing_venue:
        # Update the existing venue
        existing_venue.update(venue)
    else:
        # Add the new venue
        processed_venues.append(venue)
    
    # Save the updated list back to the file
    with open(file_path, 'w') as f:
        json.dump(processed_venues, f, indent=2)

def update_venues_with_menu_urls(input_file, output_file):
    # Load existing venues
    with open(input_file, 'r') as f:
        venues = json.load(f)

    # Set up Selenium WebDriver
    driver = setup_selenium()

    # Load already processed venues
    processed_venues = load_processed_venues(output_file)
    processed_names = {venue['name'] for venue in processed_venues}

    try:
        for venue in venues:
            # Skip if the venue has already been processed
            if venue['name'] in processed_names:
                logger.info(f"Skipping {venue['name']} - already processed")
                continue

            original_url = venue['website']
            logger.info(f"Processing {venue['name']} - {original_url}")

            # Find the menu link
            menu_url = find_menu_link(original_url, driver)

            # Update the venue's website if a menu link was found
            if menu_url != original_url:
                venue['website'] = menu_url
                logger.info(f"Updated menu URL: {menu_url}")
            else:
                logger.info("No specific menu page found. Keeping original URL.")

            # Save the processed venue
            save_processed_venue(venue, output_file)
            logger.info(f"Saved processed venue: {venue['name']}")

    finally:
        # Ensure the WebDriver is closed even if an exception occurs
        driver.quit()

    logger.info(f"All venues processed. Results saved to {output_file}")

if __name__ == "__main__":
    input_file = "../data/venues.json"
    output_file = "../data/venues_with_menu_urls.json"
    update_venues_with_menu_urls(input_file, output_file)