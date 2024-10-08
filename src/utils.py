import os
from typing import Dict, List, Any, Optional
import json
import re
from openai import OpenAI
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('openai_api_key'))


def parse_with_chatgpt(message: List[Dict[str, str]]) -> List[str]:
    """
    Parse a message using ChatGPT and return the response as a list of ingredients.

    Args:
        message (List[Dict[str, str]]): The message to be sent to ChatGPT.

    Returns:
        List[str]: The list of extracted ingredients or an empty list if an error occurs.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=message
        )

        if not response.choices or not response.choices[0].message.content:
            logger.error("Empty response from API")
            return []

        content = response.choices[0].message.content
        return content

    except Exception as e:
        logger.error(f"Error in parse_with_chatgpt: {str(e)}")
        return []


def save_json(data: Dict[str, Any], filename: str) -> None:
    """
    Save data to a JSON file.

    Args:
        data (Dict[str, Any]): The data to be saved.
        filename (str): The name of the file to save the data to.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Data saved to {filename}")
    except Exception as e:
        logger.error(f"Failed to save data to {filename}: {str(e)}")


def load_json(filename: str) -> Dict[str, Any]:
    """
    Load data from a JSON file.

    Args:
        filename (str): The name of the file to load the data from.

    Returns:
        Dict[str, Any]: The loaded data or an empty dictionary if loading fails.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"Data loaded from {filename}")
        return data
    except Exception as e:
        logger.error(f"Failed to load data from {filename}: {str(e)}")
        return {}


def handle_error(error: Exception, context: str) -> Dict[str, str]:
    """
    Handle and log errors.

    Args:
        error (Exception): The exception that occurred.
        context (str): The context in which the error occurred.

    Returns:
        Dict[str, str]: An error dictionary with context and error message.
    """
    error_message = f"Error in {context}: {str(error)}"
    logger.error(error_message)
    return {"error": error_message}


def setup_logging(name: str) -> logging.Logger:
    """
    Set up logging for a module.

    Args:
        name (str): The name of the module.

    Returns:
        logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
