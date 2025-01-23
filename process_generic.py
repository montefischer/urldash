import json
import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup
import PyPDF2

INPUT_JSON = "non_arxiv_output.json"
OUTPUT_JSON = "resources_extracted.json"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("extraction.log"),
        logging.StreamHandler()
    ]
)

def truncate_to_2000_words(text: str) -> str:
    """Utility: extract plain text up to 2000 words"""
    text = re.sub(r"\s+", " ", text)
    words = text.strip().split()
    return " ".join(words[:2000])

def extract_from_pdf(pdf_path: Path):
    """
    Extract (title, author, date, text) from PDF using PyPDF2 doc info (if available).
    Returns (title, author, date, first_2000_words).
    """
    logging.info(f"Processing PDF: {pdf_path}")
    title, author, date = "", "", ""
    text_chunks = []

    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            # Attempt metadata from the PDF's DocumentInfo
            info = reader.metadata

            # Sanitize metadata fields
            title = str(info.title) if info and hasattr(info, 'title') else ""
            author = str(info.author) if info and hasattr(info, 'author') else ""
            date = str(info.get('/CreationDate', "")) if info else ""

            # Extract text
            for n, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_chunks.append(page_text)
                if n > 20:
                    break

        full_text = " ".join(text_chunks)
        return title, author, date, truncate_to_2000_words(full_text)
    except Exception as e:
        logging.error(f"Failed to process PDF {pdf_path}: {e}")
        return title, author, date, ""


def extract_from_html(html_path: Path):
    """
    Extract (title, author, date, text) from HTML.
    Tries to find <title>, <meta name='author'>, <meta name='date'>, etc.
    Returns (title, author, date, first_2000_words).
    """
    logging.info(f"Processing HTML: {html_path}")
    title, author, date = "", "", ""

    try:
        with open(html_path, 'r', encoding='utf-8', errors='replace') as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # Title from <title>
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # Common meta tags for author/date
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta and author_meta.get("content"):
            author = author_meta["content"].strip()

        date_meta = soup.find("meta", attrs={"name": "date"})
        if date_meta and date_meta.get("content"):
            date = date_meta["content"].strip()

        # Combine text from <body> or entire HTML
        body_text = soup.get_text(" ")
        return title, author, date, truncate_to_2000_words(body_text)
    except Exception as e:
        logging.error(f"Failed to process HTML {html_path}: {e}")
        return title, author, date, ""

def process_resource(resource: dict):
    """
    Given a resource dict with keys:
      - type ('PDF' or 'HTML')
      - local_file (path to downloaded file)
    Extract the requested data and add to resource:
      - 'extracted_title'
      - 'extracted_author'
      - 'extracted_date'
      - 'extracted_text' (first 2000 words)
    """
    file_path = Path(resource["local_file"])
    logging.info(f"Processing resource: {file_path} ({resource['type']})")

    try:
        if resource["type"].upper() == "PDF":
            title, author, date, text = extract_from_pdf(file_path)
        else:
            title, author, date, text = extract_from_html(file_path)

        resource["extracted_title"] = title
        resource["extracted_author"] = author
        resource["extracted_date"] = date
        resource["extracted_text"] = text
        return resource
    except Exception as e:
        logging.error(f"Failed to process resource {file_path}: {e}")
        return resource

def main():

    logging.info("Starting resource extraction")

    # Load the original resource list
    try:
        with open(INPUT_JSON, "r", encoding="utf-8") as f:
            resources = json.load(f)
    except Exception as e:
        logging.critical(f"Failed to load input JSON {INPUT_JSON}: {e}")
        return

    # Use multiprocessing for faster extraction
    try:
        results = [process_resource(resource) for resource in resources]
    except Exception as e:
        logging.critical(f"Error processing resources: {e}")

    # Write updated resources to output JSON
    try:
        def custom_serializer(obj):
            """Convert non-serializable objects to strings."""
            return str(obj) if not isinstance(obj, (str, int, float, list, dict, bool, type(None))) else obj

        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=custom_serializer)
        logging.info(f"Extraction completed successfully. Results saved to {OUTPUT_JSON}")
    except Exception as e:
        logging.critical(f"Failed to write output JSON {OUTPUT_JSON}: {e}")

if __name__ == "__main__":
    main()
