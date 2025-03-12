import os
import csv
import re
from datetime import datetime

def format_date(date_str):
    """Converts a date string from 'Month Day, Year' to 'YYYY-MM-DD'"""
    try:
        return datetime.strptime(date_str, '%B %d, %Y').strftime('%Y-%m-%d')
    except ValueError:
        return "unknown-date"

def extract_metadata(file_path):
    """Extracts metadata (Date, URL, Title, Excerpt) from a markdown file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    metadata = {}
    
    for key in ["Date", "URL", "Title", "Excerpt"]:
        match = re.search(fr'{key}:\s*(.+)', content)
        if match:
            metadata[key.lower()] = match.group(1).strip()
    
    return metadata, content

def transform_markdown_files(csv_path, input_folder, output_folder):
    """Transforms markdown files based on CSV data and saves them in the output folder."""
    os.makedirs(output_folder, exist_ok=True)
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        next(reader)  # Skip header
        csv_data = {row[0]: row[1:] for row in reader}  # Store data as {filename: [title, slug, cover]}
    
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".md") and file_name in csv_data:
            file_path = os.path.join(input_folder, file_name)
            metadata, content = extract_metadata(file_path)
            
            if not metadata:
                continue
            
            formatted_date = format_date(metadata.get("date", ""))
            slug = csv_data[file_name][1]
            cover = csv_data[file_name][2]
            
            new_file_name = f"{formatted_date}-{slug}.md"
            new_file_path = os.path.join(output_folder, new_file_name)
            
            # Transform metadata
            transformed_content = content
            # Insert cover line after the excerpt
            transformed_content = re.sub(r'(Excerpt: .+)', r'\1\ncover: ' + cover, transformed_content, count=1)
            
            # Save the transformed file
            with open(new_file_path, 'w', encoding='utf-8') as new_file:
                new_file.write(transformed_content)
            
    print(f"Transformed markdown files saved in {output_folder}")

if __name__ == "__main__":
    csv_path = "./csv-response/with-slug.csv"
    input_folder = "./step-2"
    output_folder = "./final-blogs"
    transform_markdown_files(csv_path, input_folder, output_folder)
