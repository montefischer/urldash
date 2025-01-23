import csv
import requests
from xml.etree import ElementTree as ET
import re
import time
import logging
import json


# Logging setup
LOGFILE = "arxiv_metadata.log"
logging.basicConfig(
    filename=LOGFILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

INPUT_CSV = "bookmarks.csv"
OUTPUT_JSON = "output_tags.json"

ARXIV_API_URL = "https://export.arxiv.org/api/query?id_list="

# Rate limiting parameters
REQUESTS_PER_MINUTE = 20  # Max requests per minute to comply with policies
DELAY = 60 / REQUESTS_PER_MINUTE  # Delay in seconds between requests

def fetch_arxiv_metadata_via_api(arxiv_id):
    """
    Fetch metadata from the arXiv API using the arXiv ID.
    Returns a dictionary with title, tags, abstract, authors, and a formatted locator.
    """
    try:
        logging.info(f"Fetching metadata for arXiv ID: {arxiv_id}")
        response = requests.get(f"{ARXIV_API_URL}{arxiv_id}", timeout=10)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch metadata for {arxiv_id}, HTTP Status: {response.status_code}")
        
        # Parse the XML response
        root = ET.fromstring(response.content)
        entry = root.find("{http://www.w3.org/2005/Atom}entry")
        
        if entry is None:
            logging.warning(f"No entry found in API response for arXiv ID: {arxiv_id}")
            return {"title": "Unknown Title", "tags": [], "abstract": "", "authors": []}
        
        # Extract title
        title = entry.find("{http://www.w3.org/2005/Atom}title").text.strip()
        
        # Extract tags (categories)
        categories = entry.findall("{http://www.w3.org/2005/Atom}category")
        tags = [category.attrib["term"] for category in categories if "term" in category.attrib]

        # Extract abstract
        abstract_tag = entry.find("{http://www.w3.org/2005/Atom}summary")
        abstract = abstract_tag.text.replace("\n", " ").strip() if abstract_tag is not None else "No abstract available"

        # Extract authors
        authors = []
        for author in entry.findall("{http://www.w3.org/2005/Atom}author"):
            name = author.find("{http://www.w3.org/2005/Atom}name")
            if name is not None:
                authors.append(name.text.strip())
        
        # Extract date
        updated_tag = entry.find("{http://www.w3.org/2005/Atom}updated")
        date = updated_tag.text.strip() if updated_tag is not None else "Unknown Date"

        # Extract journal reference
        journal_ref_tag = entry.find("{http://arxiv.org/schemas/atom}journal_ref")
        journal_ref = journal_ref_tag.text.strip() if journal_ref_tag is not None else "No journal reference"

        return {
            "title": title,
            "date": date,
            "authors": authors,
            "tags": tags,
            "abstract": abstract,
            "journal": journal_ref
        }
    except Exception as e:
        logging.error(f"Error fetching metadata for arXiv ID {arxiv_id}: {e}")
        return {"title": "Error", "tags": [], "abstract": "Error", "authors": []}

def extract_arxiv_id(url):
    """
    Extract the arXiv ID from a given arXiv URL.
    Example: https://arxiv.org/abs/1234.5678 -> 1234.5678
    """
    match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)', url)
    return match.group(1) if match else None

def process_csv_with_api(input_csv, output_json):
    """
    Read input CSV, fetch metadata using the arXiv API, and save the output.
    Implements rate limiting to ensure compliance with arXiv policies.
    """
    output_data = []
    with open(input_csv, mode="r") as infile, open(output_json, mode="w", newline="") as outfile:
        reader = csv.DictReader(infile)

        for row in reader:
            url = row.get("url", "").strip()
            arxiv_id = extract_arxiv_id(url)

            if arxiv_id:
                metadata = fetch_arxiv_metadata_via_api(arxiv_id)
                output_data.append({
                    "resource_name": metadata["title"],
                    "date": metadata["date"],
                    "tags": metadata["tags"],
                    "abstract": metadata["abstract"],
                    "authors": metadata["authors"],
                    "journal": metadata["journal"],
                    "locator": f"https://arxiv.org/abs/{arxiv_id}"
                })

                logging.info(f"Processed arXiv ID: {arxiv_id} - Title: {metadata['title']} - Tags: {metadata['tags']} - Authors: {metadata['authors']}")
                # Rate limiting
                time.sleep(DELAY)
            else:
                logging.warning(f"Non-arXiv URL encountered: {url}")
        json.dump(output_data, outfile, indent=4)

if __name__ == "__main__":
    logging.info("Starting arXiv metadata processing...")
    try:
        process_csv_with_api(INPUT_CSV, OUTPUT_JSON)
        logging.info(f"Processing complete. Output saved to {OUTPUT_JSON}.")
    except Exception as e:
        logging.error(f"Unexpected error during processing: {e}")
    logging.info("Process finished.")
