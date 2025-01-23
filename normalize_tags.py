import json

def normalize_tags(data):
    """
    Normalize the tags in the dataset to ensure consistent capitalization.
    Converts all tags to lowercase.
    
    Parameters:
        data (list): List of dictionaries containing a 'tags' key.

    Returns:
        list: Updated data with normalized tags.
    """
    for entry in data:
        if "tags" in entry and isinstance(entry["tags"], list):
            # Normalize tags to lowercase
            entry["tags"] = list(set(tag.lower() for tag in entry["tags"]))
    return data

# Load JSON data from a file
input_file = "merged.json"  # Replace with your input file
output_file = "merged_normalized_tags.json"  # Replace with your desired output file

with open(input_file, "r") as f:
    data = json.load(f)

# Normalize tags
normalized_data = normalize_tags(data)

# Write normalized data to a new JSON file
with open(output_file, "w") as f:
    json.dump(normalized_data, f, indent=4)

print(f"Tags normalized. Updated file saved as {output_file}.")
