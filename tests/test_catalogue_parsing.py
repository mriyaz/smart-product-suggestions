import pytest
from src.catalogue_parsing import chunk_text, extract_products_from_response
import sys
import os

# Add the project root directory to Python's module search path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


def test_chunk_text():
    text = "This is a test text that should be split into chunks. This is a test text that should be split into chunks."
    chunks = chunk_text(text, max_chunk_size=20)

    assert len(chunks) > 1, "The text was not split into multiple chunks"
    assert all(
        len(chunk) <= 20 for chunk in chunks), "A chunk exceeds the max size"


def test_extract_products_from_response():
    response = '''```json
    [
        {"product name": "Product A"},
        {"product name": "Product B"},
        {"product name": "Product C"}
    ]
    ```'''
    products = extract_products_from_response(response)
    assert products == ["Product A", "Product B", "Product C"]
