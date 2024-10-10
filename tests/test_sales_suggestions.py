import pytest
from src.sales_suggestions import load_product_matches, create_two_column_table
import pandas as pd
import sys
import os
import json

# Add the project root directory to Python's module search path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


def test_load_product_matches(tmp_path):
    matches_file = tmp_path / "test_matches.json"
    test_data = {
        "Venue 1": ["Product A", "Product B"],
        "Venue 2": ["Product C"]
    }
    with open(matches_file, 'w') as f:
        json.dump(test_data, f)

    loaded_matches = load_product_matches(matches_file)
    assert loaded_matches == test_data


def test_create_two_column_table():
    matches = ["Product A", "Product B", "Product C", "Product D", "Product E"]
    df = create_two_column_table(matches)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (3, 2)
    assert df.iloc[2, 1] == ""  # Last cell should be empty
