# Libraries & Imports
# =================================================================
import asyncio
import pprint
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from html_chunking import get_html_chunks
import re
from collections import Counter
max_tokens = 100000
# =================================================================

def optimal_tag_finder_v1(page_source):
    # Variables
    # =================================
    tag_count = Counter()
    unique_texts = set()
    link_count = 0
    links = []
    chosen_tag = None
    chosen_count = 0
    # =================================

    print()
    print("===========================================")
    print("Finding the optimal tag to use to scrape...")
    print("===========================================")
    print()

    tag_finder_soup = BeautifulSoup(page_source, 'html.parser')
    tag_finder_soup = tag_finder_soup.find('body')
    for element in tag_finder_soup(['script','style']):
        element.decompose()
    for nav_element in tag_finder_soup('[class*="nav"], [id*="nav"]'):
        nav_element.decompose()
    unwanted_phrases = [
        "Thank you for your feedback",
        "Sorry, we failed to record your vote",
        "Sending feedback...",
        "Showing0comments",
        "There was a problem loading comments",
        "Please try again",
        "Report",
        "Showing0comments",
        "right now. Please try again later.",
        '.',
        '←Previous pageNext page→',
        "Questions? Get fast answers from reviewersWhat do you want to know about ?Please make sure that you are posting in the form of a question.Please enter a question.",
        "Need customer service?"
    ]
    unwanted_pattern = re.compile("|".join(map(re.escape, unwanted_phrases)))
    for text in tag_finder_soup.find_all(string=True):
        cleaned_text = unwanted_pattern.sub('', text)
        text.replace_with(cleaned_text.strip())
    for tag in tag_finder_soup.find_all():
        if not tag.get_text(strip=True):
            tag.decompose()
    for tag in tag_finder_soup.find_all(True):
        if not tag.find_all(True):
            current_tag = tag.get_text(strip=True)
            if current_tag and current_tag not in unique_texts:
                tag_count[tag.name] += 1
                unique_texts.add(current_tag)
        else:
            if tag.name == 'a' and tag.get('href'):
                link_count += 1
                links.append(tag['href'])
            for child in tag.children:
                if child.name:
                    child_text = child.get_text(strip=True)
                    if child_text and child_text not in unique_texts:
                        tag_count[child.name] += 1
                        unique_texts.add(child_text)
    
    tag_count_dict = dict(tag_count)
    # tags = list(tag_count_dict.keys())
    # counts = list(tag_count_dict.values)
    sorted_tags = sorted(tag_count_dict.items(), key=lambda item: item[1], reverse=True)
    container_tags = ['div', 'section', 'footer']
    for tag, count in sorted_tags:
        if tag in container_tags:
            continue 
        else:
            chosen_tag = tag
            chosen_count = count
            break
    has_link_tag = 'a' in tag_count_dict

    # Validation
    # ============================================================================
    if chosen_tag:
        print(f"The chosen tag is '{chosen_tag}' with a count of {chosen_count}.")
    else:
        print("No suitable tag found.")

    if has_link_tag:
        print("The <a> tag is present in the document.")
        a_tag_name = 'a' if 'a' in tag_count_dict else None
    else:
        print("The <a> tag is not present in the document.")
    # ============================================================================

    list_of_tags = [f'{chosen_tag}',f'{a_tag_name}']
    return list_of_tags


def extract_tags(html_content, tags: list[str]):
    """
    This takes in HTML content and a list of tags, and returns a string
    containing the text content of all elements with those tags, along with their href attribute if the
    tag is an "a" tag.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    text_parts = []
    for tag in tags:
        elements = soup.find_all(tag)
        for element in elements:
            # If the tag is a link (a tag), append its href as well
            if tag == "a":
                href = element.get('href')
                if href:
                    text_parts.append(f"{element.get_text()} ({href})")
                else:
                    text_parts.append(element.get_text())
            else:
                text_parts.append(element.get_text())
                # print(element.get_text())
    return ' '.join(text_parts)


async def ascrape_playwright(page_source) -> str:
    """
    An asynchronous Python function that uses Playwright to scrape
    content from a given URL, extracting specified HTML tags and removing unwanted tags and unnecessary
    lines.
    """
    print("Started scraping...")
    results = ""
    tags = optimal_tag_finder_v1(page_source) #returns a list
    optimal_tag = tags[0]
    print("=================================")
    print("Tags Sucessfully Found!")
    print("=================================")
    print("Tags Using:")
    print(tags)
    print("=================================")

    try:
        # Chunking and Processing the html content | Max_Tokens is 2000
        # ===================================================================
        chunks = get_html_chunks(page_source, max_tokens, is_clean_html=True)

        # ===================================================================
        # Removal of other a tags other than the reviewer's profile link ones
        # ===================================================================
        filtered_chunks = [] #chunks
        for chunk in chunks:
            soup = BeautifulSoup(chunk, 'html.parser')
            customer_review_tags = soup.find_all(lambda tag: 'customer_review' in (tag.get('id', '') + ' '.join(tag.get('class', []))))
            if 'a' in tags:
                for a_tag in soup.find_all('a'):
                    if 'a-profile' not in a_tag.get('class', []) and 'review-title' not in a_tag.get('class', []):
                        a_tag.decompose() # Remove <a> tags without 'a-profile' class
            else:pass

            for tag in customer_review_tags:
                if 'id' in tag.attrs:
                    review_id = tag['id']                    
                    # Create a new <tag> element with the optimal tag
                    new_tag = soup.new_tag(f'{optimal_tag}')
                    new_tag.string = f'customer_review-{review_id}'           
                    # Insert the <new_tag> before the current tag
                    tag.insert_before(new_tag)

            filtered_chunks.append(str(soup))

        extracted_content = [extract_tags(chunk, tags) for chunk in filtered_chunks]

        results = ' '.join(extracted_content)
        # results = '\n'.join(set(results.split('\n'))) # to remove duplicates (if any)
        results = re.sub(r'\n+', '\n', results).strip()
        # ====================================================================
        print("Content scraped")
    except Exception as e:
        results = f"Error: {e}"
    return results