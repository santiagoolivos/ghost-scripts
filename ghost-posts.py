import os
import requests
import frontmatter
import json
import mimetypes
from datetime import datetime, timezone
from urllib.parse import urljoin
import jwt
import dateutil.parser
import yaml

# Configuration
GHOST_API_URL = 'http://localhost:2368/ghost/api/admin/'
GHOST_ADMIN_API_KEY = os.getenv("GHOST_ADMIN_API_KEY")
DIRECTORY = 'step-2'



def split_api_key(api_key: str):
    """Splits the Admin API key into key_id and secret."""
    key_id, secret = api_key.split(':')
    return key_id, bytes.fromhex(secret)

def generate_jwt(api_key: str):
    """Generates a JWT token for the Ghost Admin API."""
    key_id, secret = split_api_key(api_key)
    iat = int(datetime.utcnow().timestamp())
    header = {'alg': 'HS256', 'kid': key_id}
    payload = {'iat': iat, 'exp': iat + 300, 'aud': '/admin/'}
    return jwt.encode(payload, secret, algorithm='HS256', headers=header)

def fix_yaml_format(content: str) -> str:
    """
    Ensures that titles containing colons (:) are properly quoted so YAML parsing does not break.
    """
    lines = content.splitlines()
    fixed_lines = []
    
    inside_frontmatter = False
    for line in lines:
        if line.strip() == "---":
            inside_frontmatter = not inside_frontmatter  # Toggle frontmatter section
        elif inside_frontmatter and line.startswith("Title:"):
            # Extract everything after "Title:" safely
            title_value = line.split("Title:", 1)[1].strip()
            if not title_value.startswith('"') and not title_value.startswith("'"):
                # Wrap the title in double quotes if not already quoted
                line = f'Title: "{title_value}"'
        
        fixed_lines.append(line)
    
    return "\n".join(fixed_lines)

def remove_leading_and_trailing_code_fences(content: str) -> str:
    """Removes leading/trailing markdown fences to avoid parsing issues."""
    lines = content.splitlines()
    if lines and lines[0].strip().startswith('```markdown'):
        lines.pop(0)
    while lines and lines[-1].strip() == '':
        lines.pop()
    if lines and lines[-1].strip().startswith('```'):
        lines.pop()
    return "\n".join(lines)

def upload_image_to_ghost(token: str, local_image_path: str) -> str:
    """Uploads a local image file to Ghost's /images/upload endpoint."""
    upload_url = urljoin(GHOST_API_URL, 'images/upload')
    mime_type, _ = mimetypes.guess_type(local_image_path)
    if not mime_type:
        mime_type = 'application/octet-stream'

    files = {'file': (os.path.basename(local_image_path), open(local_image_path, 'rb'), mime_type)}
    headers = {'Authorization': f'Ghost {token}', 'Accept': 'application/json'}
    response = requests.post(upload_url, headers=headers, files=files)

    if response.status_code == 201:
        return response.json()["images"][0]["url"]
    else:
        print(f"❌ Image upload failed ({response.status_code}): {response.text}")
        return None

def import_posts():
    """Processes all markdown files in DIRECTORY and posts them to Ghost."""
    total_files = 0
    successful_posts = 0
    token = generate_jwt(GHOST_ADMIN_API_KEY)
    
    
    md_files = sorted([f for f in os.listdir(DIRECTORY) if f.endswith('.md')])
    if not md_files:
        print("No .md files found in the directory.")
        return

    images_dir = 'images'
    image_files = sorted([f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg'))]) if os.path.isdir(images_dir) else []
    default_image_url = "https://static.ghost.org/v3.0.0/images/welcome-to-ghost.png"

    for idx, md_filename in enumerate(md_files):
        filepath = os.path.join(DIRECTORY, md_filename)
        total_files += 1

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_content = f.read()

            # Ensure YAML is correctly formatted
            fixed_content = fix_yaml_format(raw_content)
            cleaned_content = remove_leading_and_trailing_code_fences(fixed_content)
            post_data = frontmatter.loads(cleaned_content)

        except yaml.YAMLError as e:
            print(f"❌ YAML parsing error in '{md_filename}': {e}. Skipping this file.")
            continue
        except Exception as e:
            print(f"❌ Error processing '{md_filename}': {e}. Skipping this file.")
            continue

        raw_title = post_data.get('Title') or post_data.get('title')
        if not raw_title:
            print(f"❌ No 'Title' found in '{md_filename}'. Skipping.")
            continue

        raw_date = post_data.get('Date') or post_data.get('date')
        canonical_url = post_data.get('URL', '')
        custom_excerpt = post_data.get('Excerpt', '')

        if raw_date:
            try:
                parsed_date = dateutil.parser.parse(raw_date)
                if not parsed_date.tzinfo:
                    parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                published_date = parsed_date.isoformat()
            except (ValueError, TypeError):
                published_date = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        else:
            published_date = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()

        content = post_data.content
        tags = [{'name': 'News'}]

        # Select an image for this post based on the index (sequentially)
        feature_image_url = default_image_url
        if idx < len(image_files):
            local_image_path = os.path.join(images_dir, image_files[idx])
            uploaded_url = upload_image_to_ghost(token, local_image_path)
            if uploaded_url:
                feature_image_url = uploaded_url

        print(f"📢 Publishing '{raw_title}' with feature image: {feature_image_url}")

        payload = {
            'posts': [{
                'title': raw_title,
                'canonical_url': canonical_url,
                'custom_excerpt': custom_excerpt,
                'status': 'published',
                'published_at': published_date,
                'mobiledoc': json.dumps({
                    'version': '0.3.1',
                    'markups': [],
                    'atoms': [],
                    'cards': [['markdown', {'markdown': content}]],
                    'sections': [[10, 0]]
                }),
                'feature_image': feature_image_url,
                'tags': tags
            }]
        }

        create_post_url = urljoin(GHOST_API_URL, 'posts/')
        headers = {'Authorization': f'Ghost {token}', 'Content-Type': 'application/json'}
        response = requests.post(create_post_url, headers=headers, json=payload)
        
        if response.status_code == 201:
            successful_posts += 1
            print(f'✔️ Successfully published: {raw_title}')
        else:
            print(f'❌ Error publishing {raw_title}: {response.text}')
        
    
    print("\n📊 **Summary Report** 📊")
    print(f"📂 Total files processed: {total_files}")
    print(f"✅ Successfully published: {successful_posts}")


if __name__ == '__main__':
    import_posts()
