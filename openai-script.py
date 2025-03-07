import os
from openai import OpenAI


# Make sure you've set your OpenAI API key in the environment:
#    export OPENAI_API_KEY="sk-..."
# or replace openai.api_key = os.getenv("OPENAI_API_KEY") with your key (not recommended for security).

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(
    api_key=api_key,  # This is the default and can be omitted
)


def run_first_request(file_content: str) -> str:

    # Build the first prompt
    prompt_step1 = f"""
You are taked to write a summary of an article appearing in a legal blog. The summary will be published in a blog about Global Electronic Signature News.

Write a summary between 200 and 400 words of the following text. Prefers a straightforward and simple writing style, avoiding overly complex or pretentious language. Use active voice. Target 8th grade level. Be direct, avoid filler words.

Adopt an informative and optimistic tone, ensuring the text is conversational and accessible. Emphasize positivity and future potential, making sure the language is clear and straightforward. Avoid technical jargon unless explained and use tech-savvy terms with simple explanations.

Maintain concise and clear sentence structures, favoring short to medium-length sentences that ensure clarity and focus. Avoid corporate speak.

Identify what is the firm that published this article. Refer to this text as "recent article by [firm name]". If the human author is known, refer to this text as "article by [author] at [firm name]". Place this in the begginng of the first paragraph.

If inside the original text there is a name of a law or institution which is not in English, use the English translation (prefer the English translation if its inside the text, or produce your won). Also add the name in the original language inside parentheses, for example: Taiwan's Electronic Signatures Act (電子簽章法). This can be in excerpt and the summary.

Along with the summary, provide a title and a 10-20 word excerpt.

The title and the excerpt have to be directly related with the summary of the text, don't talk generalities. 

THIS IS IMPORTANT: Mention the firm that authored the original article in the excerpt.  Place it towards the end of the excerpt.

THIS IS IMPORTANT: Don't transcribe, but talk about the article. Use paragraphs, not bullet points.

Don't search for links.
Don't promote the firm that authored the article.

Return the results in the following format, as markdown code (enclose with code):

---
Date: [The date of the original article]
URL: [The URL of the original article]
Title: 
Excerpt: 
---
[Summary]



-- START OF THE TEXT --

{file_content}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt_step1.strip()},
        ],
    )

    return response.choices[0].message.content.strip()

def run_second_request(previous_response: str) -> str:

    # Build the second prompt with the previous response included
    prompt_step2 = f"""
Only for the body of the previous response: Link the first mention of the article (eg: recent article by...) to the original article URL. Keep the response in markdown format, enclosed as code, and containing the original frontmatter.

-- START OF THE PREVIOUS RESPONSE --

{previous_response}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt_step2.strip()},
        ],
    )

    return response.choices[0].message.content.strip()

def main():
    folder_path = "blogs-info"

    # Loop from 1 to 64, processing each .txt file if it exists
    for i in range(1, 65):
        txt_file = os.path.join(folder_path, f"{i}.txt")
        if not os.path.isfile(txt_file):
            continue  # skip if file doesn't exist

        # Read the content of the .txt
        with open(txt_file, "r", encoding="utf-8") as f:
            file_content = f.read()

        try:
            # Step 1: Run the first request
            step1_response = run_first_request(file_content)

            # Save the Step 1 response
            step1_output_file = f"{i}-step1.md"
            with open(step1_output_file, "w", encoding="utf-8") as out1:
                out1.write(step1_response)

            print(f"Saved Step 1 response to {step1_output_file}")

            # Step 2: Use the step1_response in the second request
            step2_response = run_second_request(step1_response)

            # Save the Step 2 response
            step2_output_file = f"{i}-step2.md"
            with open(step2_output_file, "w", encoding="utf-8") as out2:
                out2.write(step2_response)

            print(f"Saved Step 2 response to {step2_output_file}")

        except Exception as e:
            print(f"Error processing file {i}.txt: {e}")

if __name__ == "__main__":
    main()
