import json
import os
import time
from openai import OpenAI
import logging
from dotenv import load_dotenv
import argparse

load_dotenv()
# Set up OpenAI API key
client = OpenAI(
  api_key=os.getenv("OPENAI_API_KEY")
)

# Configuration
INPUT_DIR = "resources_extracted_segments"  # File containing the JSON objects
OUTPUT_DIR = "resources_processed_segments"  # Final transformed file
LOG_DIR = "process_log"
TOKEN_LIMIT = 2000  # Sensible limit on tokens per API call
MAX_RETRIES = 3  # Number of retries for API calls

instruction = """The following is a JSON object. Your job is to process it into a JSON object with fields title,author,date,abstract,tags. Multiple authors must be given as a list. Avoid obvious mistakes in the titles and authors. Include no text besides the processed JSON object. Incorporate all available information. Besides url,type,uuid, the other fields may be incorrect. The abstract should be of paragraph length. Use the text's own words whenever possible in the abstract. If an abstract is in the text itself, use the abstract **verbatim**, correcting any typographical errors but performing absolutely no revision of the content unless the text itself has no abstract or introduction. Remove obvious text processing artifacts. The tags should be very high-level, like "math", "finance", "blog", etc, and prefer nouns to verbs. Date should be YYYY-MM-DD when defined."""

# Function to call GPT-4 API
def transform_json_object(json_obj):
    prompt = (
        f"{instruction}\n\n"
        f"{json.dumps(json_obj, indent=2)}"
    )
    response, json_response = None, None
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a highly capable assistant. It is of critical importance that you return valid JSON responses ONLY."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=TOKEN_LIMIT
        )
        logging.info(f"Received gpt response successfully: {json_obj.get('uuid', 'unknown')}")
        json_response = json.loads(response.choices[0].message.content)
        logging.info(f"Processed JSON object successfully: {json_obj.get('uuid', 'unknown')}")
        return json_response
    except Exception as e:
        logging.error(f"Error processing JSON object {json_obj.get('uuid', 'unknown')}: {e}")
        logging.error(f"Dump response: {response}")
        return None

# Main processing function
def process_json_file(input_file, output_file, log_file):
    LOG_DIR = "process_log"
    logging.basicConfig(
        filename=os.path.join(LOG_DIR, log_file),
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info(f"Started processing {os.path.join(INPUT_DIR, args.INPUT_FILE)}.")
    # Load input file
    with open(os.path.join(INPUT_DIR, input_file), "r") as f:
        json_objects = json.load(f)

    processed_objects = []
    for i, json_obj in enumerate(json_objects):
        retries = 0
        while retries < MAX_RETRIES:
            transformed_obj = transform_json_object(json_obj)
            if transformed_obj:
                transformed_obj["url"] = json_obj["url"]
                transformed_obj["type"] = json_obj["type"]
                transformed_obj["uuid"] = json_obj["uuid"]
                processed_objects.append(transformed_obj)
                break
            else:
                retries += 1
                logging.warning(f"Retrying ({retries}/{MAX_RETRIES}) for object {i+1}...")
                time.sleep(1)  # Wait before retry

        if retries == MAX_RETRIES:
            logging.error(f"Failed to process object {i+1} after {MAX_RETRIES} retries.")


    # Save final output
    with open(os.path.join(OUTPUT_DIR, output_file), "w") as output_f:
        json.dump(processed_objects, output_f, indent=2)

    logging.info(f"Processing complete. Final output saved to {os.path.join(OUTPUT_DIR, output_file)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process a JSON file.")
    parser.add_argument("INPUT_FILE", help="Name of the input JSON file.")
    parser.add_argument("OUTPUT_FILE", help="Name of the output file.")
    parser.add_argument("LOG_FILE", help="Name of the log file.")

    args = parser.parse_args()
    process_json_file(args.INPUT_FILE, args.OUTPUT_FILE, args.LOG_FILE)
