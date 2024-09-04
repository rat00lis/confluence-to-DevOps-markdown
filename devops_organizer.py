import os
import glob
import shutil
import re
import difflib
import sys
import tqdm
import csv

def find_best_match(old_link, file_and_path, reference):
    best_match_old_link = None
    highest_similarity_old_link = 0
    
    best_match_reference = None
    highest_similarity_reference = 0
    
    for old_path, new_path in file_and_path.items():
        old_file_name = os.path.basename(old_path)
        
        similarity_old_link = difflib.SequenceMatcher(None, old_link, old_file_name).ratio()
        if similarity_old_link > highest_similarity_old_link:
            highest_similarity_old_link = similarity_old_link
            best_match_old_link = new_path
        
        similarity_reference = difflib.SequenceMatcher(None, reference, old_file_name).ratio()
        if similarity_reference > highest_similarity_reference:
            highest_similarity_reference = similarity_reference
            best_match_reference = new_path
    
    if highest_similarity_old_link >= highest_similarity_reference:
        return best_match_old_link
    else:
        return best_match_reference

def transform_to_long_path(path):
    if path.startswith('\\\\?\\'):
        return path
    return '\\\\?\\' + os.path.abspath(path)

def clean_path(path):
    clean = re.sub(r'[^\w\s.]', '', path)
    clean = clean.replace(' ', '_')
    clean = re.sub(r'_{2,}', '_', clean)
    clean = re.sub(r'\.{2,}', '.', clean)
    replacements = {
        ' ': '%20', '&': '%26', '&#x2013;': '', '_amp_': '_'
    }
    for char, code in replacements.items():
        clean = clean.replace(char, code)
    return clean

def clean_md_links(link):
    replacements = {
        ' ': '%20', '&': '%26', '&#x2013;': ''
    }
    for char, code in replacements.items():
        link = link.replace(char, code)
    return link

def get_all_mds(folder_path):
    return glob.glob(transform_to_long_path(os.path.join(folder_path, '*.md')))

def get_path_from_first_line(file_path, parent_dir):
    if file_path.endswith('index.md'):
        return os.path.join('', f'{parent_dir}.md')
    with open(transform_to_long_path(file_path), 'r', encoding='utf-8') as file:
        first_line = file.readline().strip()
        first_line = first_line.split(' > ')[1:]
        first_line = [pair.split('](') for pair in first_line]
        first_line = [(name[1:], link[:-1]) for name, link in first_line]
        
        path = parent_dir
        for name, link in first_line:
            sanitized_name = clean_path(name)
            path = os.path.join(path, sanitized_name)
        
        path = os.path.join(path, os.path.basename(file_path))
        return path

def copy_to_new_path(file_and_path, output_folder_path):
    for file_path, path in file_and_path.items():
        try:
            long_file_path = transform_to_long_path(file_path)
            long_path = transform_to_long_path(os.path.join(output_folder_path, path))
            os.makedirs(os.path.dirname(long_path), exist_ok=True)
            shutil.copy2(long_file_path, long_path)
        except PermissionError:
            continue
    
def update_internal_links_to_files(file_and_path, output_folder_path):
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^\)]+)\)')
    pattern_attachments = re.compile(r'<img[^>]*src="([^"]+)"[^>]*>')
    pattern_images = re.compile(r'<img[^>]*src="([^"]+)"[^>]*>')

    #use tqdm
    for file_path, path in tqdm.tqdm(file_and_path.items()):
        long_path = transform_to_long_path(os.path.join(output_folder_path, path))
        with open(long_path, 'r', encoding='utf-8') as file:
            content = file.read()
            links = link_pattern.findall(content)
            attachments = pattern_attachments.finditer(content)
            images = pattern_images.finditer(content)

            for link in links:
                link_text, link_url = link
                best_match = find_best_match(link_url, file_and_path, link_text)

                if best_match:
                    best_match = clean_md_links(best_match)
                    content = content.replace(link_url, f'/{best_match}')
            
            for attachment in attachments:
                src = attachment.group(1)
                src = src.replace("attachments", f"{parent_dir}/.attach")
                filename = os.path.basename(src)
                markdown_img = f'![{filename}]({src})'
                if not src.startswith('/'):
                    markdown_img = f'![{filename}](/{src})'
                if src.startswith('/attachments'):
                    markdown_img = f'![{filename}]({src.replace("/attachments", f"/{parent_dir}/.attach")})'
                content = content.replace(attachment.group(0), f'\n\n{markdown_img}\n')

            for image in images:
                src = image.group(1)
                src = src.replace("images", f"{parent_dir}/.images")
                filename = os.path.basename(src)
                markdown_img = f'![{filename}]({src})'
                if not src.startswith('/'):
                    markdown_img = f'![{filename}](/{src})'
                if src.startswith('/images'):
                    markdown_img = f'![{filename}]({src.replace("/images", f"/{parent_dir}/.images")})'
                content = content.replace(image.group(0), f'\n\n{markdown_img}\n')
        
        with open(long_path, 'w', encoding='utf-8') as file:
            file.write(content)


def add_home_pages(file_and_path, output_folder_path):
    updated = {}
    #join the path with the parent directory
    output_folder_path = os.path.join(output_folder_path, parent_dir)
    for root, dirs, files in os.walk(transform_to_long_path(output_folder_path)):
        for dir_name in dirs:
            path_to_current_dir = os.path.join(root, dir_name)
            path_to_expected_md = f'{path_to_current_dir}.md'
            md_file = transform_to_long_path(path_to_expected_md)
            if not os.path.isfile(md_file) and ".attach" not in md_file and ".images" not in md_file:
                # print(f"Creating home page for {dir_name}")
                current_files_in_the_same_path_as_dir = [os.path.join(root, file) for file in files]
                best_matches = difflib.get_close_matches(md_file, current_files_in_the_same_path_as_dir)
                # print(best_matches)
                if best_matches:
                    best_match = best_matches[0]
                    #calculate how much the best match differs from the directory name
                    similarity = difflib.SequenceMatcher(None, dir_name, os.path.basename(best_match)).ratio()
                    #if the similarity is greater than 0.8
                    if similarity > 0.8:
                        #rename the file to the directory name
                        os.rename(best_match, md_file)
                        best_match_only_title = best_match.split('\\')[-1]
                        new_file_name = md_file.split('\\')[-1]
                        for key, value in file_and_path.items():
                            value_only_title = value.split('\\')[-1]
                            if best_match_only_title == value_only_title:
                                original_text = file_and_path[key]
                                replaced_text = original_text.replace(value_only_title, new_file_name)
                                updated[key] = replaced_text
                                # print(f"Updated: {original_text} to {replaced_text}")
                    else:
                        with open(md_file, 'w') as file:
                            file.write(f"# {dir_name}\n\n")
    return updated

def move_folders(folder_path, output_folder_path, parent_dir):
    attachments_path = transform_to_long_path(os.path.join(folder_path, 'attachments'))
    images_path = transform_to_long_path(os.path.join(folder_path, 'images'))

    new_attachments_path = transform_to_long_path(os.path.join(output_folder_path, parent_dir, '.attach'))
    new_images_path = transform_to_long_path(os.path.join(output_folder_path, parent_dir, '.images'))

    # Check if the attachments folder exists and copy if it does and the destination does not exist
    if os.path.exists(attachments_path) and not os.path.exists(new_attachments_path):
        shutil.copytree(attachments_path, new_attachments_path)
    
    # Check if the images folder exists and copy if it does and the destination does not exist
    if os.path.exists(images_path) and not os.path.exists(new_images_path):
        shutil.copytree(images_path, new_images_path)



def clean_home_icon(content):
    pattern = re.compile(r'!\[.*?home.*?\.png\]\(.*?/images/.*?/.*?home.*?\.png\)')
    matches = pattern.findall(content)
    for match in matches:
        content = content.replace(match, '\n')
    return content


def main(folder_path, output_folder_path, parent_dir):
    md_files = get_all_mds(folder_path)
    file_and_path = {}

    #process files and add loading bar
    print(f'Processing files for {parent_dir}...')
    print(f'Getting paths of files...')
    for file_path in tqdm.tqdm(md_files):
        path = get_path_from_first_line(file_path, parent_dir)
        file_and_path[file_path] = path    
    copy_to_new_path(file_and_path, output_folder_path)
    print('Files copied')
    updated = add_home_pages(file_and_path, output_folder_path)
    file_and_path.update(updated)
    print('Updating internal links...')
    update_internal_links_to_files(file_and_path, output_folder_path)

    print('Moving folders...')
    move_folders(folder_path, output_folder_path, parent_dir)
    print('Done')


if __name__ == "__main__":
    folder_path = sys.argv[2]
    output_folder_path = sys.argv[1]
    #parent_dir is the name of the parent directory
    #which is the last part of the path
    parent_dir = folder_path.split('\\')[-2]
    main(folder_path, output_folder_path, parent_dir)

