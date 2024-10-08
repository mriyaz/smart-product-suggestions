import os
from typing import Dict
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Set up your OpenAI API key
client = OpenAI(api_key=os.getenv('openai_api_key'))


def parse_with_chatgpt(prompt: str, content: str) -> Dict:
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": {content}
                },
                {"role": "user", "content": prompt}
            ]
        )

        if not response.choices or not response.choices[0].message.content:
            return {"error": "Empty response from API"}

        content = response.choices[0].message.content

        # Remove code block markers and any extra content outside JSON
        content = re.sub(r'^```json\s*|\s*```$', '',
                         content, flags=re.MULTILINE)

        # Remove any text outside the JSON object
        json_start = content.find('{')
        json_end = content.rfind('}')
        if json_start == -1 or json_end == -1:
            return {"error": "Invalid JSON format in response"}

        content = content[json_start:json_end + 1]

        try:
            # Attempt to parse the sanitized content
            parsed_menu = json.loads(content)
            return parsed_menu
        except json.JSONDecodeError as json_error:
            return {"error": "Failed to parse JSON", "raw_content": content}

    except Exception as e:
        return {"error": str(e)}


def setup_logging(name: str):
    """Set up logging for a module."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger


def handle_error(error: Exception, context: str):
    """Handle and log errors."""
    logger.error(f"Error in {context}: {str(error)}")
    return {"error": f"{context}: {str(error)}"}


def save_json(data: Dict, filename: str):
    """Save data to a JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save data to {filename}: {str(e)}")


def load_json(filename: str) -> Dict:
    """Load data from a JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Data loaded from {filename}")
        return data
    except Exception as e:
        logger.error(f"Failed to load data from {filename}: {str(e)}")
        return {}
