import csv
import json

# Function to flatten JSON objects with nested lists/dictionaries
def flatten_json(json_obj, parent_key='', sep='_'):
    """Flatten nested JSON into a single dictionary."""
    items = []
    for key, value in json_obj.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_json(value, new_key, sep=sep).items())
        elif isinstance(value, list):
            if all(isinstance(i, (str, int, float)) for i in value):
                items.append((new_key, ', '.join(map(str, value))))
            else:
                for idx, item in enumerate(value):
                    items.extend(flatten_json(item, f"{new_key}[{idx}]", sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)

# Function to convert JSON to CSV
def json_to_csv(json_data, csv_file_path):
    """Convert a list of JSON objects to a CSV file."""
    # Flatten all JSON objects
    flattened_data = [flatten_json(item) for item in json_data]

    # Define the desired order of headers
    headers = ["url", "type", "title", "date", "authors", "tags", "abstract"]

    # Write to CSV
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(flattened_data)

# Example usage
if __name__ == "__main__":
    # Replace 'example.json' with the path to your JSON file
    json_file_path = "merged_normalized_tags.json"
    csv_file_path = "gappy_non_arxiv.csv"

    # Read JSON data
    with open(json_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Convert JSON to CSV
    json_to_csv(data, csv_file_path)

    print(f"CSV file has been created at: {csv_file_path}")
