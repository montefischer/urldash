import os
import json
from datetime import datetime

def parse_date(date_str):
    """Try parsing the date in various formats."""
    if not isinstance(date_str, str) or not date_str.strip():
        return date_str  # Return the original value if it's not a valid string
    formats = [
        "%B %d, %Y", "%b %d, %Y", "%B %Y", "%b %Y", 
        "%d %B %Y", "%d %b %Y", "%Y-%m-%d", "%Y-%m", "%Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str  # Return the original string if no format matches

# Directory containing JSON files
directory = "resources_processed_segments"
output_file = "merged.json"
merged_data = []

# Loop through the files and merge them
for i in range(10):  # Assuming files are named segment_0.json to segment_9.json
    file_path = os.path.join(directory, f"segment_{i}.json")
    with open(file_path, "r") as f:
        data = json.load(f)
        # Correct dates in the data
        for entry in data:
            if "date" in entry:  # Assuming the key for dates is 'date'
                entry["date"] = parse_date(entry.get("date"))
        merged_data.extend(data)

# Write the merged data to a single JSON file
with open(output_file, "w") as f:
    json.dump(merged_data, f, indent=4)
