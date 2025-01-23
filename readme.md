# urldash

Scrape, extract metadata, annotate and tag with GPT 4o-mini, and construct a lightweight tabular view of user-provided URL bookmarks. 

**Work in progress**. Plenty of hardcoded variables, bad practices, no user guide, and essentially no error handling.

Code
- `arxiv.py` - download and process arXiv links
- `generic.py` - download non-arXiv resources and associate with them uuids
- `process_generic.py` - extract text, title, author from non-arXiv resources
- `gpt_process.py` - send processed non-arXiv resources to gpt for abstract generation and fixing metadata

Data
- `bookmarks.csv` - bookmarks data containing a column of URLs
- `output_tags_clean.json` - cleaned output of `arxiv.py`
- `resources_extracted.json` - output of `process_generic.py`
- `resources_extracted_segments` - directory containing segments of `resources_extracted.json`
- `resources_processed_segments` - directory containing gpt processed segments of `resources_extracted.json`
