import json
import math
import os

def segment_json_file(input_file, output_dir, num_segments=10):
    """
    Segments a large JSON file containing an array of objects into smaller files.

    Parameters:
    - input_file (str): Path to the input JSON file.
    - output_dir (str): Directory where the smaller files will be saved.
    - num_segments (int): Number of segments/files to create.
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load the JSON data
    with open(input_file, 'r') as f:
        data = json.load(f)

    # Ensure the input is a list
    if not isinstance(data, list):
        raise ValueError("The JSON file must contain an array of objects at the root.")

    # Calculate segment size
    total_objects = len(data)
    segment_size = math.ceil(total_objects / num_segments)

    # Split and save segments
    for i in range(num_segments):
        start_idx = i * segment_size
        end_idx = min(start_idx + segment_size, total_objects)
        segment = data[start_idx:end_idx]

        if not segment:  # Stop if there's no data left to save
            break

        output_file = os.path.join(output_dir, f'segment_{i + 1}.json')
        with open(output_file, 'w') as f:
            json.dump(segment, f, indent=4)

        print(f"Segment {i + 1} saved to {output_file}")

    print("Segmentation complete!")

# Example usage
input_file = 'resources_extracted.json'  # Path to the input JSON file
output_dir = 'resources_extracted_segments'  # Directory to save the smaller files
segment_json_file(input_file, output_dir)
