from src.venue_retrieval import get_venues, save_venues
import pytest
import os
import json
import sys

# Add the project root directory to Python's module search path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


def test_get_venues():
    venues = get_venues("restaurant", "Sydney CBD, NSW 2000, Australia")
    assert len(venues) > 0
    assert all(isinstance(venue, dict) for venue in venues)
    assert all('name' in venue and 'website' in venue for venue in venues)


def test_save_venues(tmp_path):
    venues = [
        {"name": "Test Venue 1", "website": "http://test1.com"},
        {"name": "Test Venue 2", "website": "http://test2.com"}
    ]
    filename = tmp_path/"test_venues.json"
    save_venues(venues, filename)

    assert os.path.exists(filename)
    with open(filename, 'r') as f:
        loaded_venues = json.load(f)
    assert loaded_venues == venues
