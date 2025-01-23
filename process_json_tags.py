import json
import re

# Load the JSON file
with open("output_tags.json", "r") as infile:
    data = json.load(infile)

# Regex pattern for valid tags of the form subj.ABC
valid_tag_pattern = re.compile(r"^[a-z-]+\.[A-Z]+$")
# Process the JSON
for entry in data:
    entry["tags"] = [tag for tag in entry["tags"] if valid_tag_pattern.match(tag)]

# Save the filtered JSON
with open("output_tags_clean.json", "w") as outfile:
    json.dump(data, outfile, indent=4)

print("Tags have been filtered and saved to output_tags_clean.json.")
