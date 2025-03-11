import os
import csv
import re

def extract_title_from_markdown(file_path):
    """Extracts the title from a markdown file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Regex to find the Title in the metadata section
    match = re.search(r'Title:\s*(.+)', content)
    if match:
        return match.group(1).strip()
    return "Unknown Title"

def extract_numeric_part(filename):
    """Extracts the numeric part from the filename for proper sorting."""
    match = re.search(r'^(\d+)', filename)
    return int(match.group(1)) if match else float('inf')

def generate_csv_from_markdown(folder_path, output_csv):
    """Generates a CSV file with file names and titles from markdown files."""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    md_files = sorted([f for f in os.listdir(folder_path) if f.endswith(".md")], key=extract_numeric_part)
    extracted_data = []
    
    for file_name in md_files:
        file_path = os.path.join(folder_path, file_name)
        title = extract_title_from_markdown(file_path)
        extracted_data.append((file_name, title))
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["file name", "title"])
        writer.writerows(extracted_data)

if __name__ == "__main__":
    folder_path = "./step-2"  # Change this to your actual folder
    output_csv = "./csv-response/without-slug.csv"
    generate_csv_from_markdown(folder_path, output_csv)
    print(f"CSV file saved at {output_csv}")
