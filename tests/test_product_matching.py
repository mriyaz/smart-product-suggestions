import pytest
from src.product_matching import load_catalogue, extract_json_from_response
import sys
import os

# Add the project root directory to Python's module search path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


def test_load_catalogue(tmp_path):
    catalogue_file = tmp_path / "test_catalogue.csv"
    with open(catalogue_file, 'w') as f:
        f.write("Product A,Product B,Product C")

    products = load_catalogue(catalogue_file)
    assert products == ["Product A", "Product B", "Product C"]


def test_extract_json_from_response():
    response = '''```json
    {
        "Venue 1": ["Product A", "Product B"],
        "Venue 2": ["Product C"]
    }
    ```'''
    parsed_json = extract_json_from_response(response)
    assert parsed_json == {
        "Venue 1": ["Product A", "Product B"],
        "Venue 2": ["Product C"]
    }
