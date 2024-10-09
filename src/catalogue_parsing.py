import re
import json
import PyPDF2
import logging
from typing import List, Dict
from utils import parse_with_chatgpt

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def chunk_text(text: str, max_chunk_size: int = 5000) -> List[str]:
    """
    Split the text into chunks of approximately max_chunk_size characters.

    Args:
        text (str): The input text to be chunked.
        max_chunk_size (int): The maximum size of each chunk.

    Returns:
        List[str]: A list of text chunks.
    """
    chunks = []
    current_chunk = ""
    for line in text.split("\n"):
        if len(current_chunk) + len(line) < max_chunk_size:
            current_chunk += line + "\n"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = line + "\n"
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks


def extract_products_from_response(response: str) -> List[str]:
    """
    Extract product names from the ChatGPT response, handling various formats.

    Args:
        response (str): The response from ChatGPT.

    Returns:
        List[str]: A list of product names.
    """
    # Remove any non-printable characters
    content = re.sub(r'[^\x20-\x7E]', '', response)

    # Extract content between code blocks if present
    if content.strip().startswith("```") and content.strip().endswith("```"):
        content = content.strip().split("```")[1]
        if content.lower().startswith("json"):
            content = content[4:].strip()

    products = []

    # Try parsing as JSON
    try:
        data = json.loads(content)
        if isinstance(data, list):
            products = [item.get('product name') for item in data if isinstance(
                item, dict) and 'product name' in item]
        elif isinstance(data, dict):
            products = [data.get('product name')
                        ] if 'product name' in data else []
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract product names using regex
        logger.warning(
            "JSON parsing failed. Attempting to extract product names using regex.")
        product_matches = re.findall(r'"product name":\s*"([^"]+)"', content)
        products = product_matches

    # If no products found, log the content for debugging
    if not products:
        logger.error(
            f"No products extracted. Response content: {content[:500]}...")

    # Remove any None values and strip whitespace
    products = [p.strip() for p in products if p]

    return products


def parse_pdf_catalogue(pdf_file: str) -> List[str]:
    """
    Parse the PDF catalogue and extract product names.

    Args:
        pdf_file (str): Path to the PDF catalogue file.

    Returns:
        List[str]: A list of product names.
    """
    with open(pdf_file, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ' '.join(page.extract_text() for page in reader.pages)

    chunks = chunk_text(text)
    all_products = set()

    for i, chunk in enumerate(chunks):
        prompt = f"""
        Extract product names from the following catalogue text. 
        Format the output as a JSON list of objects, each with a 'product name' key.
        
        Text for extraction:\n\n{chunk}
        """
        message = [
            {"role": "system", "content": "You are a helpful assistant that extracts product names from catalogues."},
            {"role": "user", "content": prompt}
        ]

        try:
            response = parse_with_chatgpt(message)
            products = extract_products_from_response(response)
            all_products.update(products)
            logger.info(f"Extracted {len(products)} products from chunk {i+1}")
        except Exception as e:
            logger.error(f"Error processing chunk {i+1}: {e}")
            logger.error(f"Problematic chunk content: {chunk[:500]}...")

    return sorted(list(all_products))


def save_catalogue(products: List[str], output_file: str):
    """
    Save the parsed catalogue to a CSV file.

    Args:
        products (List[str]): List of product names.
        output_file (str): Path to the output CSV file.
    """
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        f.write(','.join(products))
    logger.info(f"Catalogue saved to {output_file}")


if __name__ == "__main__":
    pdf_file = '../data/PremierQualityFoodsBrochure2021.pdf'
    output_file = '../data/catalogue.csv'
    products = parse_pdf_catalogue(pdf_file)
    save_catalogue(products, output_file)
    print(f"Catalogue parsing completed. Results saved to {output_file}")
