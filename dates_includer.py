
import sys
import os
import csv
import re
import difflib
import tqdm

html_title_to_md_title={}

def get_html_titles_and_path(html_directory):
    #make an os walk for all the files in the html directories
    html_titles_and_path = {}
    for root, dirs, files in tqdm.tqdm(os.walk(html_directory)):
        for file in files:
            if file.endswith(".html"):
                try:
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        content = f.read()
                        # RegEx for the page title
                        pattern = r'<span id="title-text">\s*(.*?)\s*</span>'
                        try:
                            file_title = re.search(pattern, content).group(1)
                            html_titles_and_path[file_title] = os.path.join(root, file)
                        except AttributeError:
                            #skip to the next file
                            continue
                except UnicodeDecodeError:
                    with open(os.path.join(root,file), 'r', encoding='latin') as f:
                        content = f.read()
                        # RegEx for the page title
                        pattern = r'<span id="title-text">\s*(.*?)\s*</span>'
                        try:
                            file_title = re.search(pattern, content).group(1)
                            html_titles_and_path[file_title] = os.path.join(root, file)
                        except AttributeError:
                            #skip to the next file
                            continue
                except:
                    continue
                              
    return html_titles_and_path

def get_md_titles_and_path(md_directory):
    #make an os walk for all the files in the md directories
    md_titles_and_path = {}
    for root, dirs, files in tqdm.tqdm(os.walk(md_directory)):
        for file in files:
            if file.endswith(".md"):
                md_titles_and_path[file] = os.path.join(root, file)
    return md_titles_and_path

def clean_names(name):
    #clean name should be all lowercase, and all together
    #cut name so its only the right part of the :
    if ':' in name:
        name = name.split(':')[-1]
    name = name.lower()
    name = name.replace(' ', '')
    name = name.replace('_', '')
    name = name.replace('-', '')
    name = name.replace('.md', '')
    return name

def find_best_match(html_title, md_titles_and_path):
    html_title_clean = clean_names(html_title)
    
    # Create a cleaned version of the dictionary
    md_titles_and_path_clean = {clean_names(key): key for key in md_titles_and_path.keys()}
    
    # Get the closest matches with at least 80% similarity
    matches = difflib.get_close_matches(html_title_clean, md_titles_and_path_clean.keys(), n=1, cutoff=0.8)
    
    # Return the original value of the best match if found, otherwise return None
    if matches:
        original_key = md_titles_and_path_clean[matches[0]]
        html_title_to_md_title[html_title_clean] = matches[0]
        return md_titles_and_path[original_key]
    else:
        return None

def find_date_in_html(html_file_content):
    page_metadata_pattern = re.compile(r'<div class="page-metadata">(.*?)</div>', re.DOTALL)
    metadata = page_metadata_pattern.search(html_file_content)
    if metadata:
        try:
            entire_match = metadata.group(1)
            HTML_tags_pattern = re.compile(r'<.*?>')
            metadata_clean = re.sub(HTML_tags_pattern, '', entire_match)
            metadata_clean = metadata_clean.replace("\n", "")
            #delete all spaces until a letter is found
            for i in range(len(metadata_clean)):
                if metadata_clean[i].isalpha():
                    metadata_clean = metadata_clean[i:]
                    break
            return f"\n###### {metadata_clean}"
        except AttributeError:
            return ""

    return ""

def assign_html_to_md(html_titles_and_path, md_titles_and_path):
    # Assign the html files to the md files and return a dictionary with the html file path as key and the md file path as value
    html_to_md = {}
    for html_title, html_path in tqdm.tqdm(html_titles_and_path.items()):
        md_title = find_best_match(html_title, md_titles_and_path)
        if md_title:
            html_to_md[html_path] = md_title
    
    return html_to_md

import shutil

def write_dates_in_mds(html_to_md, output_directory):
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # Write the dates in the md files
    for html_path, md_path in tqdm.tqdm(html_to_md.items()):
        with open(html_path, 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()
            date = find_date_in_html(html_content)
        
        # Determine the new path for the md file in the output directory
        relative_md_path = os.path.relpath(md_path, start=os.path.commonpath(html_to_md.values()))
        new_md_path = os.path.join(output_directory, relative_md_path)
        
        # Create the necessary subdirectories in the output directory
        os.makedirs(os.path.dirname(new_md_path), exist_ok=True)
        
        # Copy the original md file to the new output directory
        shutil.copy(md_path, new_md_path)
        
        with open(new_md_path, 'r', encoding='utf-8') as md_file:
            md_content = md_file.read()
            if "###### created by" in md_content:
                md_content = re.sub(r'###### created by.*?on.*?\n', date, md_content)
            else:
                md_content += date
        
        with open(new_md_path, 'w', encoding='utf-8') as md_file:
            md_file.write(md_content)


html_directories = sys.argv[1]
md_directories = sys.argv[2]
output_directory = sys.argv[3]

print("Getting HTML titles and paths...")
html_titles_and_path = get_html_titles_and_path(html_directories)
print("Getting MD titles and paths...")
md_titles_and_path = get_md_titles_and_path(md_directories)

print("Assigning HTML files to MD files...")
html_to_md = assign_html_to_md(html_titles_and_path, md_titles_and_path)

print("Writing dates in MD files...")
write_dates_in_mds(html_to_md, output_directory)

#save the html_title_to_md_title dictionary
#in the output directory
with open(os.path.join(output_directory, 'html_title_to_md_title.csv'), 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, delimiter=';')
    for key, value in html_title_to_md_title.items():
        csvwriter.writerow([key, value])