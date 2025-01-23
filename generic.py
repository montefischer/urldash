import os
import csv
import uuid
import json
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import argparse

PDF_DIR = "downloaded_pdfs"
HTML_DIR = "downloaded_html"
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(HTML_DIR, exist_ok=True)


LOGFILE = "generic_metadata.log"
BOOKMARKS_CSV = "bookmarks.csv"
DOWNLOAD_LOG_CSV = "download_log.csv"
OUTPUT_JSON = "non_arxiv_output.json"

def read_urls_from_csv(file_path: str) -> list:
    try:
        df = pd.read_csv(file_path)
        if 'url' not in df.columns:
            raise ValueError("CSV must contain a 'url' column.")
        return df['url'].tolist()
    except Exception as e:
        logging.error(f"Failed to read CSV {file_path}: {e}")
        return []

def read_download_log_csv(log_file: str) -> dict:
    """
    Returns a dict of {url: {"type": ..., "uuid": ...}}.
    """
    download_log = {}
    if not os.path.exists(log_file):
        return download_log
    try:
        with open(log_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                url = row["url"]
                download_log[url] = {
                    "type": row["filetype"],
                    "uuid": row["uuid"]
                }
    except Exception as e:
        logging.error(f"Failed to read download log {log_file}: {e}")
    return download_log

def write_download_log_csv(log_file: str, download_log: dict):
    """
    download_log: {url: {"type": ..., "uuid": ...}}
    Writes CSV with columns: [url, filetype, uuid]
    """
    try:
        with open(log_file, mode="w", encoding="utf-8", newline="") as f:
            fieldnames = ["url", "filetype", "uuid"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for url, info in download_log.items():
                writer.writerow({
                    "url": url,
                    "filetype": info["type"],
                    "uuid": info["uuid"]
                })
    except Exception as e:
        logging.error(f"Failed to write download log {log_file}: {e}")

def download_resource(url: str) -> tuple[bytes, str]:
    """
    Returns (content, content_type) or (None, None) on error.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/117.0.5938.132 Safari/537.36"
        )
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        return response.content, content_type
    except Exception as e:
        logging.error(f"Failed to download {url}: {e}")
        return None, None
    
def extract_html_title(content: bytes) -> str:
    """
    Extract the <title> tag from HTML. Returns 'Untitled' if not found.
    """
    try:
        soup = BeautifulSoup(content, "html.parser")
        title_tag = soup.find("title")
        return title_tag.get_text(strip=True) if title_tag else "Untitled"
    except Exception as e:
        logging.error(f"Failed to extract HTML title: {e}")
        return "Untitled"

def extract_pdf_title(content: bytes) -> str:
    try:
        with open("temp.pdf", "wb") as f:
            f.write(content)
        reader = PdfReader("temp.pdf")
        title = reader.metadata.get('/Title', None)
        os.remove("temp.pdf")
        return str(title) if title else "Unknown Title"
    except Exception as e:
        logging.error(f"Failed to extract PDF title: {e}")
        return "Unknown Title"

def process_urls(
    input_csv: str,
    log_csv: str,
    output_json: str
):
    """
    - Reads URLs from input_csv.
    - Skips those containing 'arxiv.org'.
    - If URL is already in log_csv, use the local file for reprocessing (text extraction + summary).
    - Otherwise, download the URL, updated log_csv, and process text.
    - Writes final processed data to output_json.
    """

    # Load data
    urls = read_urls_from_csv(input_csv)
    download_log = read_download_log_csv(log_csv)
    results = []

    for url in urls:
        # Skip arxiv
        if "arxiv.org" in url:
            logging.info(f"Skipping arxiv.org URL: {url}")
            continue

        # Check log to see if we already have a record
        if url in download_log:
            logging.info(f"Already have a local file for {url}, reprocessing text.")
            filetype = download_log[url]["type"]
            file_uuid = download_log[url]["uuid"]

            if filetype.lower() == "pdf":
                pdf_path = os.path.join(PDF_DIR, file_uuid)
                if not os.path.exists(pdf_path):
                    logging.error(f"Logged PDF path not found: {pdf_path}")
                    continue
                with open(pdf_path, "rb") as f:
                    content = f.read()

                title = extract_pdf_title(content)

                results.append({
                    "url": url,
                    "type": "PDF",
                    "uuid": file_uuid,
                    "title": title,
                    "local_file": pdf_path,
                })

            elif filetype.lower() == "html":
                html_path = os.path.join(HTML_DIR, file_uuid)
                if not os.path.exists(html_path):
                    logging.error(f"Logged HTML path not found: {html_path}")
                    continue
                with open(html_path, "rb") as f:
                    content = f.read()

                # Extract and summarize
                title = extract_html_title(content)
                results.append({
                    "url": url,
                    "type": "HTML",
                    "uuid": file_uuid,
                    "title": title,
                    "local_file": html_path,
                })

            else:
                logging.error(f"Unknown filetype for {url} in download_log.")
            continue

        # Otherwise, we need to download
        logging.info(f"Downloading {url}")
        content, content_type = download_resource(url)

        if not content:
            logging.error(f"No content downloaded for {url}")
            continue

        if "application/pdf" in content_type:
            # PDF
            file_uuid = f"{uuid.uuid4()}.pdf"
            pdf_path = os.path.join(PDF_DIR, file_uuid)
            try:
                with open(pdf_path, "wb") as f:
                    f.write(content)

                download_log[url] = {"type": "PDF", "uuid": file_uuid}

                # Extract and summarize
                title = extract_pdf_title(content)
                results.append({
                    "url": url,
                    "type": "PDF",
                    "title": title,
                    "local_file": pdf_path,
                })
            except Exception as e:
                logging.error(f"Failed to save/process PDF for {url}: {e}")

        elif "text/html" in content_type:
            # HTML
            file_uuid = f"{uuid.uuid4()}.html"
            html_path = os.path.join(HTML_DIR, file_uuid)
            try:
                with open(html_path, "wb") as f:
                    f.write(content)

                download_log[url] = {"type": "HTML", "uuid": file_uuid}

                title = extract_html_title(content)

                results.append({
                    "url": url,
                    "type": "HTML",
                    "title": title,
                    "local_file": html_path,
                })
            except Exception as e:
                logging.error(f"Failed to save/process HTML for {url}: {e}")

        else:
            logging.warning(f"Unsupported content type for {url}: {content_type}")
            continue

    try:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        logging.info(f"Results saved to {output_json}")
    except Exception as e:
        logging.error(f"Failed to save results to JSON: {e}")

    write_download_log_csv(log_csv, download_log)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download urls",
    )
    parser.add_argument(
        "--input_csv",
        default=BOOKMARKS_CSV,
        help=f"Path to the input csv file containing urls to downnload. Default is '{BOOKMARKS_CSV}'."
    )
    parser.add_argument(
        "--output_json",
        default=OUTPUT_JSON,
        help=f"Path to the output JSON file where results will be saved. Default is '{OUTPUT_JSON}'."
    )
    parser.add_argument(
        "--log_csv",
        default=DOWNLOAD_LOG_CSV,
        help=f"Path to log of previously downloaded files. Default is {DOWNLOAD_LOG_CSV}"
    )

    args = parser.parse_args()

    logging.basicConfig(
        filename=args.log_csv,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Example usage
    process_urls(
        input_csv=args.input_csv,
        log_csv=args.log_csv,
        output_json=args.output_json
    )
