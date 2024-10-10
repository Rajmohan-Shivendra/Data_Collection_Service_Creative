# env: .dockerSpiderEnv\Scripts\activate
# command to run docker: docker run --name dockerized_spider_8 -v C:\Polytechnic_web_crawler_with_docker:/output  data_collection_dker
# Libraries & Imports
# =================================================================
from playwright.async_api import async_playwright
from schemas import aws_review_schema as aws_rev
from extraction_openAI import main_dict_changes
from scrape import ascrape_playwright
import asyncio
import pprint
from bs4 import BeautifulSoup
import json
import os
import gzip
import pandas as pd
from datetime import datetime
import time
import re
import ast
# =================================================================

# Get Google Sheets Function
# ==========================
def get_googleSheet(country):
    sheet_id = '1rtm2u33CqNeBesCSVvJG73Dcwi3hEtleuiZZue0noyc'
    sheet_name = country
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)
# ==========================

# Save Output Function
# ========================================================================
def save_output(lor:list):
    asin = lor[0].get("Info", {}).get("info", {}).get("asin")
    print(asin)
    print(lor[0])
    output_dir = f"/output/amz-us-reviews/dd={datetime.now().day}" # by default us
    os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist
    json_filename = os.path.join(output_dir, f"{asin}.json")
    gz_filename = os.path.join(output_dir, f"{asin}.json.gz")
    # save as .json
    with open(json_filename, 'w', encoding='utf-8') as json_file:
        json.dump(lor, json_file, indent=1)

    if os.path.exists(gz_filename):
        os.remove(gz_filename)
    
    # compress .json file into .gz file
    with open(json_filename, 'rb') as json_file:
        with gzip.open(gz_filename, 'wb') as gz_file:
            gz_file.writelines(json_file)

    # Remove the uncompressed .json file | Cleanup
    os.remove(json_filename)
# ========================================================================


# Dataframe Loading
# ========================================
df = get_googleSheet('us') #by default us
amazon_links = df['Amazon page link']
asins = df['ASIN']
pdt_names = df['Product Name']
sku = df['SKU']
# ========================================

# Data Processing/Cleaning
# ========================================
def data_cleaning(extracted_content, html_content:str, **kwargs):
    max_retries = 1
    retries = 0
    cleaned_content = None

    while retries < max_retries:
        try:
            cleaned_content = extracted_content.strip("()").strip("`").replace("json\n", "")
            print()
            print("Cleaned Content")
            print("---------------")
            print(cleaned_content)
            print("---------------")
            print()

            reviews = json.loads(cleaned_content)
            return reviews  # Return the reviews if successful

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            retries += 1
            print(f"Retrying {retries}/{max_retries}...")
            print()
            print("Extracting content")
            print("----------------------")
            print()
            extracted_content = main_dict_changes(**kwargs,
                                        content=html_content)
            pprint.pprint(extracted_content)
            print()
            print("-----------------------")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break  # Break the loop on unexpected errors

    print("Max retries reached. Could not process the content.")
    print("Extracting data at hand....")
    return None  # Return None or handle the failure case as needed
# ========================================

def remove_duplicates(lst):
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result

def extract_review_data(soup: BeautifulSoup, data_dict: dict):

    extracted_data = {
        'reviewer_names': [],
        'reviewer_ids': [],
        'review_titles': [],
        'review_bodies': [],
        'review_ratings': [],
        'review_dates': [],
        'reviewer_accounts': []
    }

    def find_elements(tag, selector):
        elements = None

        # Try finding elements by class first
        if 'class' in selector:
            elements = soup.find_all(tag, class_=selector['class'])
            print("Printing Elements here")
            print('-----------------------')
            print(tag)
            print(selector)
            print(elements)
            print('-----------------------')

            # If no elements found, try the same value as 'id'
            if not elements and 'class' in selector:
                elements = soup.find_all(tag, id=selector['class'])
                print("Printing Elements here")
                print('-----------------------')
                print(tag)
                print(selector)
                print(elements)
                print('-----------------------')

            # If still no elements found, try the same value as 'href_contains'
            if not elements and 'class' in selector:
                elements = soup.find_all(tag, href=re.compile(selector['class']))
                print("Printing Elements here")
                print('-----------------------')
                print(tag)
                print(selector)
                print(elements)
                print('-----------------------')

        elif 'id' in selector:
            elements = soup.find_all(tag, id=selector['id'])
            print("Printing Elements here")
            print('-----------------------')
            print(tag)
            print(selector)
            print(elements)
            print('-----------------------')
            # If no elements found, try the same value as 'class'
            if not elements and 'id' in selector:
                elements = soup.find_all(tag, class_=selector['id'])
                print("Printing Elements here")
                print('-----------------------')
                print(tag)
                print(selector)
                print(elements)
                print('-----------------------')
            # If still no elements found, try the same value as 'href_contains'
            if not elements and 'id' in selector:
                elements = soup.find_all(tag, href=re.compile(selector['id']))
                print("Printing Elements here")
                print('-----------------------')
                print(tag)
                print(selector)
                print(elements)
                print('-----------------------')
        elif 'href_contains' in selector:
                elements = soup.find_all(tag, href=re.compile(selector['href_contains']))
                print("Printing Elements here")
                print('-----------------------')
                print(tag)
                print(selector)
                print(elements)
                print('-----------------------')

        return elements

    for key, value in data_dict.items():
        tag = value['tag']
        selector = value['selector']
        
        elements = find_elements(tag, selector)
        
        if not elements:
            print("Printing Selectors and Tags in If not Elements")
            print("----------------------------------------------")
            print(tag)
            print(selector)
            print(elements)
            continue

        for element in elements:
            element_text = element.text.strip()
            if key == 'Reviewer Name':
                extracted_data['reviewer_names'].append(element_text)
            elif key == 'Reviewer ID':
                extracted_data['reviewer_ids'].append(element.get('href'))
            elif key == 'Review Title':
                extracted_data['review_titles'].append(element_text)
            elif key == 'Review Body':
                extracted_data['review_bodies'].append(element_text)
            elif key == 'Review Rating':
                extracted_data['review_ratings'].append(element_text)
            elif key == 'Reviewer Amazon Account':
                extracted_data['reviewer_accounts'].append(element.get('href'))
            elif key == 'Review Date':
                pattern = r"Reviewed in the United States on \w+ \d{1,2}, \d{4}"
                match = re.search(pattern, element_text)
                if match:
                    extracted_data['review_dates'].append(element_text)
                else:
                    # Ignore non-US reviews
                    continue

    return extracted_data

async def scrape_with_playwright(start_url: str,info_data: dict, lor: list, **kwargs):
    
    if lor is None:
            lor = []

    async with async_playwright() as p:

        custom_headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.52 Safari/537.36',
        }

        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_extra_http_headers(custom_headers)
        url = start_url

        while True:
            await page.goto(url, wait_until='domcontentloaded')
            page_source = await page.content()
            html_content= await ascrape_playwright(page_source)#, tags)
            
            print("html_content")
            print("----------------------")
            print(html_content)
            print("----------------------")

            print("Length of html_content")
            print("----------------------")
            print(len(html_content))
            print("----------------------")
            # break

            print("Extracting content")
            print("----------------------")
            print()
            extracted_content = main_dict_changes(**kwargs,
                                        content=html_content)
            pprint.pprint(extracted_content)
            print()
            print("-----------------------")

            # Loading Files
            # ==============================================================================
            # loading dictionary
            with open("/output/temp_dict.py", 'r') as file:
                content = file.read()
                content = content.split('=', 1)[1].strip() #remove the 'data_dict =' parts
                data_dict = ast.literal_eval(content)
            # loading html content
            with open('/output/html_content.txt', 'r', encoding='utf-8') as file:
                page = file.read()
            soup = BeautifulSoup(page, 'html.parser')
            # ===============================================================================

            extracted_data = {
                'reviewer_names': [],
                'reviewer_ids': [],
                'review_titles': [],
                'review_bodies': [],
                'review_ratings': [],
                'review_dates': [],
                'reviewer_accounts': []
            }

            # Extracting Content
            # ==============================================================================
            data = extract_review_data(soup, data_dict)
            reviewer_names = data['reviewer_names']
            reviewer_ids = data['reviewer_ids']
            review_titles = data['review_titles']
            review_bodies = data['review_bodies']
            review_ratings = data['review_ratings']
            review_dates = data['review_dates']
            reviewer_accounts = data['reviewer_accounts']
            # ==============================================================================

            # Removal of duplicated instances (if any)
            # ======================================================
            reviewer_names = remove_duplicates(reviewer_names)
            reviewer_ids = remove_duplicates(reviewer_ids)
            review_titles = remove_duplicates(review_titles)
            reviewer_accounts = remove_duplicates(reviewer_accounts)
            # ======================================================

            # Subsetting incase if non us data collected
            # ======================================================
            length_of_dates = len(review_dates)
            reviewer_names = reviewer_names[:length_of_dates]
            reviewer_ids = reviewer_ids[:length_of_dates]
            review_titles = review_titles[:length_of_dates]
            review_bodies = review_bodies[:length_of_dates]
            review_ratings = review_ratings[:length_of_dates]
            reviewer_accounts = reviewer_accounts[:length_of_dates]
            # ======================================================

            print("Printing Length of Lists")
            print(f"reviewer_names - {len(reviewer_names)}")
            print(f"reviewer_ids - {len(reviewer_ids)}")
            print(f"review_titles - {len(review_titles)}")
            print(f"review_bodies - {len(review_bodies)}")
            print(f"review_ratings - {len(review_ratings)}")
            print(f"reviewer_accounts - {len(reviewer_accounts)}")
            print(f"review_dates - {len(review_dates)}")

            # ==============================================================================

            # Filtering Ids, URLS
            # ==============================================================================
            reviewer_ids = [
                re.sub(r'.*/gp/customer-reviews/([^/]+)/.*', r'\1', url) if 'customer-reviews' in url else 
                re.sub(r'.*/gp/profile/amzn1\.account\.([^/]+).*', r'\1', url).strip('.') 
                for url in reviewer_ids
            ]
            reviewer_accounts = [
                re.sub(r'.*/gp/customer-reviews/([^/]+)/.*', r'\1', url) if 'customer-reviews' in url else 
                re.sub(r'.*/gp/profile/amzn1\.account\.([^/]+).*', r'\1', url).strip('.') 
                for url in reviewer_accounts
            ]
            # reviewer_names = reviewer_names[2:]
            # review_dates = review_dates[2:]
            # ==============================================================================

            # Formatting Reviews
            # ==============================================================================
            num_reviews = len(reviewer_names)
            for i in range(num_reviews):
                review = {
                    'Reviewer Name': reviewer_names[i],
                    'Reviewer ID': f"https://www.amazon.com/product-review/{reviewer_ids[i]}",
                    'Review Title': review_titles[i],
                    'Review Body': review_bodies[i],
                    'Review Rating': review_ratings[i],
                    'Review Date': review_dates[i],
                    'Reviewer Account': f"https://www.amazon.com/gp/profile/amzn1.account.{reviewer_accounts[i]}",
                    'Info': info_data
                }
                lor.append(review)
            reviews_json = json.dumps(lor, indent=4)
            print(reviews_json)
            break
            # ==============================================================================

            # break
            # Cleaning Content
            # ==============================================================================
            # reviews = data_cleaning(extracted_content, html_content, **kwargs)

            # if reviews != None:
            #     for review in reviews:
            #         review_id = review["Reviewer's ID"]
            #         parts = review_id.split('-')
            #         review["Reviewer's ID"] = f"{parts[-1]}"
            #         review["Customer Reivew Link"] = f"https://www.amazon.com/product-review/{parts[1]}"
            #         review['Reviewer Link'] = f"https://www.amazon.com{review['Reviewer Link'].rstrip('.')}"
            #         review['Info'] = info_data

            #     lor.extend(reviews)
            # else:
            #     pass #move on to paginition, will skip review of this page

            # ==============================================================================
            # Paginition (Works)
            # ==============================================================================
            # async with async_playwright() as p:

            #     # Variables for Paginiton
            #     # =======================
            #     max_pages = 2
            #     page_count = 0
            #     # =======================

            #     soup = BeautifulSoup(page_source, 'html.parser')
            #     next_button = soup.select_one('li.a-last a')
            #     print(next_button)
            #     if page_count >= max_pages:
            #         # limit to only scrape a maximum of 2 pages per product
            #         print("Max 2 Pages Scraped")
            #         break
            #     else:
            #         if next_button and 'href' in next_button.attrs:
            #             next_page_url = 'https://www.amazon.com' + next_button['href']
            #             url = next_page_url 
            #             print("URL PRINTING")
            #             print("------------")
            #             print(url)
            #             print("------------")
            #             time.sleep(30)
            #             page_count = page_count + 1
            #             if page_count >= max_pages:
            #                 # limit to only scrape a maximum of 2 pages per product
            #                 print("Max 2 Pages Scraped")
            #                 break
            #         else:
            #             # No more pages to scrape, break the loop
            #             print("No more pages to scrape.")
            #             break
            # ==============================================================================
    await browser.close()
    

    # save overall output
    # ====================================================
    if lor:
        save_output(lor)
    else:
        print("Unable To Extract Content from Product")
    # ====================================================

# Main Script
# ========================================================
for base_url, asins, pdt_names, sku in zip(amazon_links, asins, pdt_names, sku):
    max_pages = 2
    page_count = 1
    lor = [] # list of reviews

    info_data = {
        "info": {
            "marketplace": "us", # by default US
            "sub_category": f"{pdt_names}",
            "asin": f"{asins}",
            "sku": f"{sku}",
            "category": f"{pdt_names}",
            "brand": "Creative", # by default Creative
            "product_name": f"{pdt_names}"
        }
    }

    while page_count <= max_pages:
        print()
        print(f"Going to Page {page_count}...")
        print()
        # base_url can be used for product scarping (pdt_url)
        # assuming us is always chosen can modify later
        review_url = f"https://www.amazon.com/product-reviews/" + asins + f"?pageNumber={page_count}&sortBy=recent&formatType=current_format"
        print("Scraping from url: " + base_url)
        print(f"Entering URL - {review_url}")
        asyncio.run(scrape_with_playwright(
            start_url = review_url,
            info_data = info_data,
            lor = lor,
            schema=aws_rev
        ))
        page_count = page_count + 1
        time.sleep(30) # wait for 30 seconds

    # break
# ========================================================