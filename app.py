import streamlit as st
import pandas as pd
import requests
import json
from bs4 import BeautifulSoup
import time
from concurrent.futures import ThreadPoolExecutor

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

# Function to process a single row
def process_row(row, api_key, cse_id):
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

    return {'Keyword 1': keyword1, 'Keyword 2': keyword2, 'SERP Similarity': similarity_percentage}

# Function to process the input CSV and generate the output CSV with SERP similarity
def process_file(file, api_key, cse_id, progress_bar, progress_text, table_placeholder):
    df = pd.read_csv(file)

    # Ensure the input CSV has the correct columns
    if not {'Keyword 1', 'Keyword 2'}.issubset(df.columns):
        raise ValueError("Input CSV must contain 'Keyword 1' and 'Keyword 2' columns")

    # Initialize the output DataFrame
    output_df = pd.DataFrame(columns=['Keyword 1', 'Keyword 2', 'SERP Similarity'])

    total_rows = len(df)
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(process_row, row, api_key, cse_id): index for index, row in df.iterrows()}

        for future in futures:
            index = futures[future]
            result = future.result()
            new_row = pd.DataFrame([result])
            output_df = pd.concat([output_df, new_row], ignore_index=True)

            # Update progress bar and text
            progress_bar.progress((index + 1) / total_rows)
            progress_text.text(f"Processing row {index + 1} of {total_rows}")

            # Update the table in the placeholder
            table_placeholder.write(output_df)

    return output_df

# Streamlit app layout
def main():
    st.title("SERP Similarity Checker")

    st.markdown("""
    ## About the App
    Upload a CSV with two columns: 'Keyword 1' and 'Keyword 2'. The app will search Google for both keywords and calculate the SERP similarity percentage.
    """)

    # Use Streamlit secrets for API key and CSE ID
    api_key = st.secrets.get("GOOGLE_API_KEY")
    cse_id = st.secrets.get("CUSTOM_SEARCH_ENGINE_ID")

    uploaded_file = st.file_uploader("Upload your file", type=["csv"])

    # Start button - Only show this if a file is uploaded
    if uploaded_file is not None:
        if st.button('Start Processing'):
            # Ensure API key and CSE ID are available
            if api_key and cse_id:
                # Initialize progress bar, progress text, and table placeholder
                progress_bar = st.progress(0)
                progress_text = st.empty()
                table_placeholder = st.empty()

                # Process the file
                processed_data = process_file(uploaded_file, api_key, cse_id, progress_bar, progress_text, table_placeholder)

                st.write("Processed Data:")
                st.write(processed_data)

                # Download button
                st.download_button(
                    label="Download processed data",
                    data=processed_data.to_csv(index=False),
                    file_name="serp_similarity_output.csv",
                    mime="text/csv",
                )
            else:
                st.error("API Key or Custom Search Engine ID is missing.")

if __name__ == "__main__":
    main()
