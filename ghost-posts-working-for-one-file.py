import os
import requests
import frontmatter
import json
from datetime import datetime
from urllib.parse import urljoin
import jwt
import dateutil.parser
from datetime import datetime, timezone
# Configuration
GHOST_API_URL = 'http://localhost:2368/ghost/api/admin/'
GHOST_ADMIN_API_KEY = os.getenv("GHOST_ADMIN_API_KEY")
DIRECTORY = 'step-2'

def split_api_key(api_key: str):
    """
    Splits the Admin API key into key_id and secret.
    """
    key_id, secret = api_key.split(':')
    return key_id, bytes.fromhex(secret)

def generate_jwt(api_key: str):
    """
    Generates a JWT token for the Ghost Admin API.
    """
    key_id, secret = split_api_key(api_key)
    iat = int(datetime.utcnow().timestamp())
    header = {'alg': 'HS256', 'kid': key_id}
    payload = {
        'iat': iat,
        'exp': iat + 300,  # Token is valid for 5 minutes
        'aud': '/admin/'
    }
    token = jwt.encode(payload, secret, algorithm='HS256', headers=header)
    return token

def remove_leading_and_trailing_code_fences(content: str) -> str:
    """
    Removes a leading ``` (code fence) and its matching
    trailing ``` fence if they exist at the very start/end of the file.
    """
    lines = content.splitlines()
    # If the very first line starts with triple backticks, remove lines until we find a matching closing
    if lines and lines[0].strip().startswith('```markdown'):
        # Remove the first line (leading fence)
        lines.pop(0)
        # # Remove lines until we find a closing fence or run out
        # while lines and not lines[0].strip().startswith('```'):
        #     lines.pop(0)
        # # Remove the closing fence line itself if present
        # if lines and lines[0].strip().startswith('```'):
        #     lines.pop(0)

    # Similarly, check if the very last line is a triple fence
    while lines and lines[-1].strip() == '':
        lines.pop()  # remove trailing empty lines if any
    if lines and lines[-1].strip().startswith('```'):
        lines.pop()  # remove trailing fence

    return "\n".join(lines)

def import_posts():
    """
    Processes ONLY the first markdown file in DIRECTORY,
    extracts front matter fields and content,
    and posts them to Ghost as a published post.
    """
    token = generate_jwt(GHOST_ADMIN_API_KEY)
    headers = {
        'Authorization': f'Ghost {token}',
        'Content-Type': 'application/json'
    }

    md_files = [f for f in os.listdir(DIRECTORY) if f.endswith('.md')]
    if not md_files:
        print("No .md files found in the directory.")
        return

    # Take ONLY the first .md file found
    first_file = md_files[0]
    filepath = os.path.join(DIRECTORY, first_file)

    with open(filepath, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    # 1) Remove leading/trailing code fences (if the file was stored with ```markdown blocks)
    cleaned_content = remove_leading_and_trailing_code_fences(raw_content)
    print("Cleaned content:", cleaned_content)

    # 2) Load with frontmatter
    post_data = frontmatter.loads(cleaned_content)
    print("Front matter content:", post_data)


    # Extract values from front matter
    raw_title = post_data.get('Title') or post_data.get('title')
    print(f"Title: {raw_title}")
    raw_date = post_data.get('Date') or post_data.get('date')
    canonical_url = post_data.get('URL', '')
    custom_excerpt = post_data.get('Excerpt', '')

    # If title is missing, we can't publish
    if not raw_title:
        print(f"❌ No 'Title' found in '{first_file}'. Cannot publish.")
        return

    # Parse 'Date' into ISO 8601
    if raw_date:
        try:
            parsed_date = dateutil.parser.parse(raw_date)

            # If no tzinfo was provided, assume it's UTC
            if not parsed_date.tzinfo:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)

            # Convert to ISO 8601 with an offset, e.g. 2024-09-27T00:00:00+00:00
            published_date = parsed_date.isoformat()
        except (ValueError, TypeError):
            # Fallback if the date is unparseable
            published_date = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
    else:
        published_date = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
        
    content = post_data.content

    # Build the payload for Ghost
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
                'cards': [
                    [
                        'markdown',
                        {
                            'markdown': content
                        }
                    ]
                ],
                'sections': [[10, 0]]
            })
        }]
    }

    # Post to Ghost Admin API
    url = urljoin(GHOST_API_URL, 'posts/')
    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 201:
        print(f'✔️ Successfully published: {raw_title}')
    else:
        print(f'❌ Error publishing {raw_title}: {response.text}')

if __name__ == '__main__':
    import_posts()
