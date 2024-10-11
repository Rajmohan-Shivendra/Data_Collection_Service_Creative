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



# Used to find the tags that will help with scraping.
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

    # Main Unwanted phrases to remove when checking for optimal
    # Tags
    # ================================================================    
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
    # ================================================================    

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
    container_tags = ['div','section', 'footer']
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
# =================================================================



# Remove tags that contains keywords in their attributes that we 
# do not need
# =================================================================
def contains_unwanted_keywords(id_or_class: str) -> bool:
    unwanted_keywords = ['row','column','nav', 'footer', 'header', 'shortcut',
                         'spacing','button','a-list-item','a-color-state','cr',
                         'block','declarative','disabled','vote','col']
    return any(keyword in id_or_class for keyword in unwanted_keywords)
# =================================================================


# Remove Attirbutes that contains too many attributes,
# remove based on the maximum number of attributes and the
# length of the overall attributes of a tag
# =================================================================
def is_too_complex(element) -> bool:
    """Check if the element has too many attributes or long attributes."""
    max_attributes = 5  # Set a threshold for the number of attributes
    max_length = 300  # Set a threshold for the total length of attribute strings
    attributes = element.attrs
    if len(attributes) > max_attributes:
        print("Printing of Attirbutes that exceed Length")
        print(attributes)
        return True
    total_length = sum(len(f"{key}={value}") for key, value in attributes.items())
    return total_length > max_length
# =================================================================



# This function is used to retrieve the content that we need
# to feed the openai, while also retaining their parent's
# attributes, (i.e, Class, ID, Data-hook)
# =================================================================
def extract_tags_with_html(html_content, tags: list[str]):
    """
    This function takes HTML content and a list of tags, 
    returning the HTML for those tags. 
    It includes the parent tag's 
    id/class, removes empty tags, skips unwanted 
    tags with certain IDs or
    classes, and filters out overly complex elements.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    html_parts = []
    pattern = r"Reviewed in the United States on \w+ \d{1,2}, \d{4}"

    for tag in tags:
        elements = soup.find_all(tag)
        for element in elements:

            if tag == 'a':
                # print("a has been found")
                href = element.get('href', '')
                # Ensure href is captured before potentially filtering out
                new_tag = f'<{tag} href="{href}">{element_text}</{tag}>'
                html_parts.append(new_tag)
                continue

            if is_too_complex(element):
                continue

            element_text = element.get_text(strip=True)

            if not element_text:  
                continue

            parent = element.parent
            parent_id = parent.get('id', '')
            parent_data_hook = parent.get('data-hook',[])
            parent_class = parent.get('class', [])

            # Skip if parent ID or any class contains unwanted keywords
            if contains_unwanted_keywords(parent_id) or \
               any(contains_unwanted_keywords(cls) for cls in parent_class):
                continue

            # Skip specific unwanted spans based on content
            if ((element_text in ['5 star', '4 star', '3 star', '2 star', '1 star'] or
                 element_text.endswith('%'))):
                continue
            
            if re.search(pattern, element_text):# to find review dates
                 new_tag = f'<{tag} id="review-date">{element_text}</{tag}>'
                 html_parts.append(new_tag)
                 continue

            if parent_data_hook:
                new_tag = f'<{tag} id="{parent_data_hook}">{element_text}</{tag}>'
            elif parent_id:
                new_tag = f'<{tag} id="{parent_id}">{element_text}</{tag}>'
            elif parent_class:
                parent_class_str = ' '.join(parent_class)
                new_tag = f'<{tag} class="{parent_class_str}">{element_text}</{tag}>'
            else:
                new_tag = str(element)
            html_parts.append(new_tag)

    return '\n'.join(html_parts)
# =================================================================



# Used to remove tags with specific attributes
# =================================================================
def remove_tags_with_attribute(soup: BeautifulSoup, keywords: list[str]):
    tags_to_remove = soup.find_all(lambda tag: tag.name and
                                     any(keyword.lower() in str(value).lower() for value in tag.attrs.values() for keyword in keywords))
    for tag in tags_to_remove:
        tag.decompose()
# =================================================================



# Main Function
# =================================================================
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
        # Only use the Body contents of the html page
        soup = BeautifulSoup(page_source, 'html.parser')
        remove_tags_with_attribute(soup, ['average-star-rating','cm_cr-rvw_summary','a-list-item','a-color-state','cr-product-byline'])
        page_source = str(soup.body)

        # Chunking and Processing the html content | Max_Tokens is 2000
        # ===================================================================
        chunks = get_html_chunks(page_source, max_tokens, is_clean_html=True,attr_cutoff_len=54)

        extracted_content = [extract_tags_with_html(chunk, tags) for chunk in chunks]

        results = ' '.join(extracted_content)
        results = re.sub(r'\n+', '\n', results).strip()
        # Writing HTML Contents to a .txt file
        # ====================================================================
        file_path = "/output/html_content.txt"

        with open(file_path, 'w') as file:
            file.write(results)

        print(f"Results have been written to {file_path}")
        # ====================================================================
        print("Content scraped")
    except Exception as e:
        results = f"Error: {e}"
    return results
# =================================================================
