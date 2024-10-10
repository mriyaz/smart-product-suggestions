import re
import csv
import json
import logging
from src.utils import parse_with_chatgpt

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_catalogue(catalogue_file):
    """
    Load the catalogue from a CSV file.

    :param catalogue_file: Path to the CSV file containing the catalogue
    :return: List of product names
    """
    products = []
    try:
        with open(catalogue_file, 'r', newline='') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                products.extend(row)
        return products
    except Exception as e:
        logger.error(f"Error loading catalogue: {e}")
        return []


def extract_json_from_response(response):
    """
    Extract JSON content from the ChatGPT response.

    :param response: ChatGPT response string
    :return: Parsed JSON object or None if parsing fails
    """
    # Try to extract JSON from code block
    json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response)
    if json_match:
        json_content = json_match.group(1)
    else:
        # If no JSON block is found, use the entire response
        json_content = response

    # Remove any leading/trailing whitespace and newlines
    json_content = json_content.strip()

    try:
        return json.loads(json_content)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON content: {json_content}")
        return None


def match_products_venue(venue, products):
    """
    Match ingredients for a single venue to potential products using ChatGPT.

    :param venue: Dictionary containing venue name and ingredients
    :param products: List of product names
    :return: Dictionary of matched products for the venue
    """
    prompt = f"Given the following venue names and their ingredients, along with the product catalog, match the ingredients to "\
        f"the products. If there is a match, either by direct match or through synonyms of the ingredients, format the output "\
        f"as a JSON object. The key should be the venue name, and the value should be a list of matched product names based on "\
        f"both exact and synonymous ingredient matches."\
        f"\n\nVenue: {json.dumps(venue)}\n\nProducts: {products}"
    message = [
        {"role": "system", "content": "You are a helpful assistant that matches venue ingredients to suitable products."},
        {"role": "user", "content": prompt}
    ]
    try:
        response = parse_with_chatgpt(message)
        # logger.info(f"Matched Products response: {response}")

        parsed_json = extract_json_from_response(response)
        if parsed_json:
            return parsed_json
        else:
            logger.error("Failed to extract valid JSON from the response")
            return {}
    except Exception as e:
        logger.error(f"Error matching products: {e}")
        return {}


def process_product_matching(ingredients_file, catalogue_file, output_file):
    """
    Process ingredient lists and match them to products from the catalogue.

    :param ingredients_file: JSON file containing derived ingredients
    :param catalogue_file: CSV file containing the catalogue
    :param output_file: Output file to save product matches
    """
    try:
        with open(ingredients_file, 'r') as f:
            venue_ingredients = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing ingredients file: {e}")
        return
    except FileNotFoundError:
        logger.error(f"Ingredients file not found: {ingredients_file}")
        return

    products = load_catalogue(catalogue_file)

    if not products:
        logger.error(
            "No products loaded from the catalogue. Aborting product matching.")
        return

    all_matches = {}

    for venue in venue_ingredients:
        matches = match_products_venue(venue, products)
        all_matches.update(matches)

    try:
        with open(output_file, 'w') as f:
            json.dump(all_matches, f, indent=2)
        logger.info(
            f"Product matching completed. Results saved to {output_file}")
    except IOError as e:
        logger.error(f"Error writing to output file: {e}")


if __name__ == "__main__":
    ingredients_file = '../data/ingredients.json'
    catalogue_file = '../data/catalogue.csv'
    output_file = '../data/product_matches.json'
    process_product_matching(ingredients_file, catalogue_file, output_file)
