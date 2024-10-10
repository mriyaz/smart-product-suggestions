import pytest
from src.menu_url_retrieval import find_menu_link, load_processed_venues, save_processed_venue
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import json
import sys
import os

# Add the project root directory to Python's module search path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


@pytest.fixture
def mock_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(options=chrome_options)


def test_find_menu_link(mock_driver):
    url = "https://www.example.com"
    menu_link = find_menu_link(url, mock_driver)
    assert isinstance(menu_link, str)
    assert menu_link.startswith("http")


def test_load_processed_venues(tmp_path):
    file_path = tmp_path / "test_processed_venues.json"
    test_data = [{"name": "Test Venue", "website": "http://test.com"}]
    with open(file_path, 'w') as f:
        json.dump(test_data, f)

    loaded_data = load_processed_venues(file_path)
    assert loaded_data == test_data


def test_save_processed_venue(tmp_path):
    file_path = tmp_path / "test_processed_venues.json"
    venue = {"name": "New Venue", "website": "http://new.com"}
    save_processed_venue(venue, file_path)

    with open(file_path, 'r') as f:
        saved_data = json.load(f)
    assert venue in saved_data
