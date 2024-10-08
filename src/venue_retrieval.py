# Import required libraries
import configparser
import json
import requests
import os

# Load configuration
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(
    os.path.dirname(__file__)), 'config.ini')


if not os.path.exists(config_path):
    raise FileNotFoundError(f"Config file not found at {config_path}")

config.read(config_path)

if 'GooglePlaces' not in config:
    raise KeyError("'GooglePlaces' section not found in config file")

try:
    GOOGLE_PLACES_API_KEY = config['GooglePlaces']['api_key']
except KeyError:
    raise KeyError(
        "'api_key' not found in 'GooglePlaces' section of config file")

if not GOOGLE_PLACES_API_KEY:
    raise ValueError("Google Places API key is empty")

print("API key loaded successfully")

# Define constants
GOOGLE_PLACES_API_URL = "https://places.googleapis.com/v1/places:searchText"


def get_venues(query, location):
    """
    Retrieve venues using Google Places API v1.

    :param query: Type of venue (e.g., "restaurant", "cafe", "bar")
    :param location: Location to search (e.g., "Sydney CBD")
    :return: List of venues
    """
    # Set up the header for the API request
    headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': GOOGLE_PLACES_API_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.websiteUri'

    }

    data = {
        'textQuery': f"{query} in {location}"
    }

    print(f"Sending request for {query} in {location}")
    response = requests.post(GOOGLE_PLACES_API_URL, headers=headers, json=data)
    print(f"Response status code: {response.status_code}")

    if response.status_code != 200:
        print(f"Error response: {response.text}")
        return []

    # Parse the JSON response
    data = response.json()
    print(f"Number of results: {len(data.get('places', []))}")

    # Initialize an empty list to store venue information
    venues = []

    # Convert the response to a Python dictionary
    for place in data.get('places', []):
        print(f"Processing place: {place}")

        # if place['websiteUri'] exists, then add to venues
        if 'websiteUri' in place:
            venue = {
                'name': place['displayName']['text'],
                'website': place['websiteUri']
            }
            venues.append(venue)

    # Return the list of venues
    return venues


def save_venues(venues, filename):
    """
    Save venues to a JSON file.

    :param venues: List of venue dictionaries
    :param filename: Name of the file to save
    """
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    # Open the file in write mode
    with open(filename, 'a') as file:
        # Use json.dump() to write the venues list to the file
        json.dump(venues, file, indent=4)


def main():
    # Set the location (Sydney CBD)
    location = "Sydney CBD, NSW 2000, Australia"
    # Define a list of venue types to search for
    venue_types = ["restaurant", "cafe", "bar"]

    # Initialize an empty list to store all venues
    all_venues = []

    # Loop through each venue type
    for venue_type in venue_types:
        print(f"\nSearching for {venue_type}s...")
        #   Call get_venues() for each type
        venues = get_venues(venue_type, location)
        print(f"Found {len(venues)} {venue_type}s")
        #   Extend the all_venues list with the results
        all_venues.extend(venues)

    # Use an absolute path for saving the file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_file = os.path.join(project_root, 'data', 'venues.json')

    # Save the combined results to a JSON file
    save_venues(all_venues, output_file)
    # Print a message indicating how many venues were retrieved and saved
    print(f"Retrieved and saved {len(all_venues)} venues.")


if __name__ == "__main__":
    # Call the main function
    main()
