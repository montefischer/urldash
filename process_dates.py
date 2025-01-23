import json
from datetime import datetime

def reformat_dates(input_file, output_file):
    def parse_date(date_str):
        """Try parsing the date in various formats."""
        formats = [
            "%B %d, %Y",  # Full month name, day, year (e.g., January 16, 2025)
            "%b %d, %Y",  # Abbreviated month name, day, year (e.g., Jan 12, 2025)
            "%B %Y",      # Full month name and year (e.g., January 2025)
            "%b %Y",      # Abbreviated month name and year (e.g., Jan 2025)
            "%d %B %Y",   # Day, full month name, year (e.g., 18 March 2022)
            "%d %b %Y",   # Day, abbreviated month name, year (e.g., 18 Mar 2022)
            "%Y-%m-%d",   # ISO format (e.g., 2025-01-16)
            "%Y-%m",      # Year and month (e.g., 2025-01)
            "%Y"          # Year only (e.g., 2025)
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return date_str  # Return the original string if no format matches

    with open(input_file, 'r') as f:
        data = json.load(f)

    for entry in data:
        if 'date' in entry and entry['date']:
            entry['date'] = parse_date(entry['date'])

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    input_file = "resources_processed_segments/segment_1.json"  # Replace with your input file name
    output_file = "resources_processed_segments/segment_1_datefix.json"  # Replace with your output file name
    reformat_dates(input_file, output_file)
    print(f"Dates reformatted and saved to {output_file}")
