import streamlit as st
import json
import math
from src.utils import parse_with_chatgpt
import pandas as pd


def load_product_matches(file_path):
    """
    Load product matches from a JSON file.

    :param file_path: Path to the JSON file containing product matches
    :return: Dictionary of venue names and their product matches
    """
    with open(file_path, 'r') as f:
        product_matches = json.load(f)

    # Check if the loaded data is already in the correct format
    if isinstance(product_matches, dict):
        return product_matches

    # If it's a list of dictionaries, convert it to the desired format
    elif isinstance(product_matches, list):
        return {venue.get('name', venue.get('venue_name', 'Unknown')): venue.get('product_matches', []) for venue in product_matches}

    # If it's neither a dict nor a list, raise an error
    else:
        raise ValueError(f"Unexpected data structure in {file_path}")


def generate_sales_suggestion(venue_name, product_matches):
    """
    Generate a sales suggestion using ChatGPT based on the product matches for a venue.

    :param venue_name: Name of the venue
    :param product_matches: Product matches for the venue
    :return: Generated sales suggestion
    """
    prompt = f"Create a short sales pitch to a restaurant,bar or cafe such as {venue_name} to sell the following product :\n\n{json.dumps(product_matches, indent=2)}\n\nProvide a conversational suggestion in a professional manner, on which products to pitch and why they would be suitable for this venue."
    message = [
        {"role": "system", "content": "You are a helpful sales assistant providing product sales pitch for food distributors."},
        {"role": "user", "content": prompt}
    ]

    response = parse_with_chatgpt(message)

    # The response is now a string, so we can return it directly
    return response


def create_two_column_table(matches):
    """
    Create a two-column table from the list of matches.

    :param matches: List of product matches
    :return: Pandas DataFrame with two columns
    """
    # Calculate the number of rows needed
    num_rows = math.ceil(len(matches) / 2)

    # Create two columns
    col1 = matches[:num_rows]
    col2 = matches[num_rows:] + [''] * (num_rows - len(matches[num_rows:]))

    # Create DataFrame
    df = pd.DataFrame({
        "Product Matches 1": col1,
        "Product Matches 2": col2
    })

    return df


def main():
    st.title("Smart Product Match & Sales Pitch for Food Distributors")

    try:
        product_matches = load_product_matches('data/product_matches.json')
    except Exception as e:
        st.error(f"Error loading product matches: {str(e)}")
        return

    # Create a dropdown menu for venue selection
    venue_names = list(product_matches.keys())
    selected_venue = st.selectbox("Select a venue:", [""] + venue_names)

    if selected_venue:
        st.subheader(f"Product Matches for {selected_venue}")

        # Display product matches in a table
        matches = product_matches[selected_venue]
        df = create_two_column_table(matches)
        st.table(df)

        st.subheader("Sales Pitch")

        # Add a spinner while generating the suggestion
        with st.spinner('Generating sales pitch...'):
            suggestion = generate_sales_suggestion(
                selected_venue, matches)

        # Display the suggestion after it's generated
        st.write(suggestion)


if __name__ == "__main__":
    main()
