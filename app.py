import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
import time

# Function to perform a search using the Google Custom Search API
def search(query, api_key, cse_id):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': query,
        'key': api_key,
        'cx': cse_id,
    }

    for attempt in range(5):  # Retry up to 5 times
        try:
            response = requests.get(url, params=params)
            if response.status_code == 429:  # Rate limit hit
                time.sleep(10)  # Wait for 10 seconds before retrying
                continue
            response.raise_for_status()  # Raise an exception for HTTP errors
            return json.loads(response.text)
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}, attempt {attempt + 1}/5")
            time.sleep(5)  # Wait for 5 seconds before retrying
    return {}  # Return an empty dictionary if all attempts fail

# Function to extract URLs from search results
def extract_urls(results):
    urls = []
    if 'items' in results:
        for item in results['items']:
            link = item.get('link')
            if link:
                urls.append(link)
    return urls[:10]

# Function to calculate SERP similarity percentage
def calculate_serp_similarity(urls1, urls2):
    set1 = set(urls1)
    set2 = set(urls2)
    common_urls = set1.intersection(set2)
    similarity_percentage = (len(common_urls) / 10) * 100  # Calculate the percentage based on top 10 results
    return similarity_percentage

# Function to process the input CSV and generate the output CSV with SERP similarity
def process_file(input_file, output_file, api_key, cse_id):
    df = pd.read_csv(input_file)

    # Ensure the input CSV has the correct columns
    if not {'Keyword 1', 'Keyword 2'}.issubset(df.columns):
        raise ValueError("Input CSV must contain 'Keyword 1' and 'Keyword 2' columns")

    # Initialize the output DataFrame
    output_df = pd.DataFrame(columns=['Keyword 1', 'Keyword 2', 'SERP Similarity'])

    for index, row in df.iterrows():
        keyword1 = row['Keyword 1']
        keyword2 = row['Keyword 2']

        # Perform Google searches for both keywords
        results1 = search(keyword1, api_key, cse_id)
        results2 = search(keyword2, api_key, cse_id)

        # Extract URLs from search results
        urls1 = extract_urls(results1)
        urls2 = extract_urls(results2)

        # Calculate SERP similarity percentage
        similarity_percentage = calculate_serp_similarity(urls1, urls2)

        # Append the results to the output DataFrame
        output_df = output_df.append({'Keyword 1': keyword1, 'Keyword 2': keyword2, 'SERP Similarity': similarity_percentage}, ignore_index=True)

    # Save the output DataFrame to a CSV file
    output_df.to_csv(output_file, index=False)

# Main function to run the script
def main():
    api_key = "YOUR_GOOGLE_API_KEY"
    cse_id = "YOUR_CUSTOM_SEARCH_ENGINE_ID"
    input_file = "input_keywords.csv"
    output_file = "serp_similarity_output.csv"

    process_file(input_file, output_file, api_key, cse_id)
    print(f"Output saved to {output_file}")

if __name__ == "__main__":
    main()