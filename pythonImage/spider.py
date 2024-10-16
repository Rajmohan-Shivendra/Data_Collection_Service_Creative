# env: .dockerSpiderEnv\Scripts\activate
# command to run docker: docker run -v C:\Polytechnic_web_crawler_with_docker:/output data_collection_dker python spider.py --country_code es
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
import requests
import argparse
from deep_translator import GoogleTranslator
from dateutil import parser
# =================================================================

# country codes
# =========================
country_dict = {
    'es': 'Spain',
    'us': 'United States',
    'fr': 'France',
    'de': 'Germany',
    'jp': 'Japan',
    'se': 'Sweden',
    'it': 'Italy',
    'nl': 'Netherlands',
    'ca': 'Canada',
    'uk': 'United Kingdom',
}
# =========================


# Date Patterns
# ================================
date_patterns = [
    r'\b\d{1,2}/\d{1,2}/\d{4}\b',         # Matches 19/12/2021, 12/19/2021, etc.
    r'\b\d{1,2}-\d{1,2}-\d{4}\b',         # Matches 19-12-2021, 12-19-2021, etc.
    r'\b\d{1,2} \w+ \d{4}\b',             # Matches 19 December 2021
    r'\b\w+ \d{1,2}, \d{4}\b',            # Matches December 19, 2021
    r'\b\w+ \d{1,2} \d{4}\b',             # Matches December 19 2021
    r'\w+ \d{1,2}, \d{4}',
]
# ================================


# Global Variables - Unused
# ===========================
#gc = {} # global level cache
# ===========================

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


# Removing Duplicated Data from List
# ========================================
def remove_duplicates(lst):
    keywords_to_ignore = ['Amazon Customer','Amazon Client',
                          'Amazon Consumer','Amazon Shopper']
    seen = set()
    result = []
    for item in lst:
        item = GoogleTranslator(source='auto', target='en').translate(item)
        if item in keywords_to_ignore:
            continue
        if item not in seen:
            result.append(item)
            seen.add(item)
    return result
# ========================================


# Extraction of Review Data frm Dictionary
# ========================================
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

    def find_elements(key,tag, selector):
        elements = None
        element_tag = None
        og_tag = None

        # Try finding elements by class first
        if 'class' in selector:
            elements = soup.find_all(tag, class_=selector['class'])
            print("Printing Elements here")
            print('-----------------------')
            print(tag)
            print(selector)
            print(elements)
            element_tag = 'class'
            og_tag = 'class'
            print('-----------------------')

            # If no elements found, try the same value as 'id'
            if not elements and 'class' in selector:
                elements = soup.find_all(tag, id=selector['class'])
                print("Printing Elements here")
                print('-----------------------')
                print(tag)
                print(selector)
                print(elements)
                element_tag = 'id'
                print('-----------------------')

            # If still no elements found, try the same value as 'href_contains'
            if not elements and 'class' in selector:
                elements = soup.find_all(tag, href=re.compile(selector['class']))
                print("Printing Elements here")
                print('-----------------------')
                print(tag)
                print(selector)
                print(elements)
                element_tag = 'href_contains'
                print('-----------------------')

        elif 'id' in selector:
            elements = soup.find_all(tag, id=selector['id'])
            print("Printing Elements here")
            print('-----------------------')
            print(tag)
            print(selector)
            print(elements)
            element_tag = 'id'
            og_tag = 'id'
            print('-----------------------')
            # If no elements found, try the same value as 'class'
            if not elements and 'id' in selector:
                elements = soup.find_all(tag, class_=selector['id'])
                print("Printing Elements here")
                print('-----------------------')
                print(tag)
                print(selector)
                print(elements)
                element_tag = 'class'
                print('-----------------------')

            # If still no elements found, try the same value as 'href_contains'
            if not elements and 'id' in selector:
                elements = soup.find_all(tag, href=re.compile(selector['id']))
                print("Printing Elements here")
                print('-----------------------')
                print(tag)
                print(selector)
                print(elements)
                element_tag = 'href_contains'
                print('-----------------------')

        elif 'href_contains' in selector:
                elements = soup.find_all(tag, href=re.compile(selector['href_contains']))
                print("Printing Elements here")
                print('-----------------------')
                print(tag)
                print(selector)
                print(elements)
                element_tag = 'href_contains'
                og_tag = 'href_contains'
                print('-----------------------')

        data_dict[key]['selector'] = {f'{element_tag}': f"{selector[f'{og_tag}']}"}
        print(f"Dictionary Updated from {og_tag} to {element_tag}")
        return elements

    for key, value in data_dict.items():
        tag = value['tag']
        selector = value['selector']
        
        elements = find_elements(key,tag,selector)
        
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
                print("Reviewer Name If Statement Entered")
                extracted_data['reviewer_names'].append(element_text)
            elif key == 'Reviewer ID':
                print("Reviewer ID If Statement Entered")
                extracted_data['reviewer_ids'].append(element.get('href'))
            elif key == 'Review Title':
                print("Review Title If Statement Entered")
                extracted_data['review_titles'].append(element_text)
            elif key == 'Review Body':
                print("Review Body If Statement Entered")
                extracted_data['review_bodies'].append(element_text)
            elif key == 'Review Rating':
                print("Review Rating If Statement Entered")
                extracted_data['review_ratings'].append(element_text)
            elif key == 'Reviewer Amazon Account':
                print("Reviewer Amazon Account If Statement Entered")
                extracted_data['reviewer_accounts'].append(element.get('href'))
            elif key == 'Review Date':
                print("Review Date If Statement Entered")
                pattern = f"{country_dict[cc]} on "
                combined_pattern = pattern + '(' + '|'.join(date_patterns) + ')'
                print(combined_pattern)
                # pattern = r"Reviewed in the United States on \w+ \d{1,2}, \d{4}"
                translated_result = GoogleTranslator(source='auto', target='en').translate(element_text)
                match = re.search(combined_pattern, translated_result)
                if match:
                    print("Appending Review Dates to Extracted Data")
                    extracted_data['review_dates'].append(element_text)
                else:
                    # Ignore non-US reviews
                    continue

    return extracted_data
# ========================================



# Obtaining Dictionary if it is alrdy been loaded before
# ===========================================================================================
def get_dictionary_for_product(lc:dict, pid:str, html_content, cache_timeout=3600, **kwargs):
    current_time = time.time()
    if pid in lc and (current_time - lc[pid]['timestamp']) < cache_timeout:
        print("Using cached dictionary")
        return lc[pid]['dict'],lc
    else:
        print("Calling OpenAI to generate a dictionary")
        extracted_content = main_dict_changes(**kwargs,
                                    content=html_content)
        
        # attempt global cache (unused)
        # ===============================================================================================================================
        # if not gc: #if cache not empty
        #     # check if the extracted content is existing in the global cache
        #     if extracted_content in gc and (current_time - gc[extracted_content]['timestamp']) < (cache_timeout*2):
        #         print("Found Matching Dictionary")
        #         gc[extracted_content] = {"count":(gc[extracted_content]['count'])+1, 'timestamp': current_time}
        #         print("Global Cache Appended")

        #         if gc[extracted_content]['count'] >= 3: # if the cache has been the same throughout 3 products continue to use it for the rest
        #             with open('/output/cache_approv.txt', 'w') as f:
        #                 f.write(extracted_content)
        #                 print("Dict as Cache Saved Successfully!!")
        #     else:
        #         gc = {} #reset
        #         gc[extracted_content] = {"count":1, 'timestamp': current_time}

        #         if os.path.exists('/output/cache_approv.txt'):
        #             os.remove('/output/cache_approv.txt')
        #             print("Cache File deleted successfully.")
        #         else:
        #             print("Cache does not exist.")

        #         print("Global Cache Resetted")

        # else:  # if cache empty
        #     gc[extracted_content] = {"count":1, 'timestamp': current_time}
        #     print("New Cache Created")
        # ===============================================================================================================================

    lc[pid] = {'dict': extracted_content, 'timestamp': current_time}
    return extracted_content,lc
# ===========================================================================================



# Main Scrape Function (Where it all starts)
# ====================================================================================
async def scrape_with_playwright(start_url: str,info_data: dict, lor: list,lc:dict, **kwargs):
    temp_file_dir = "/output/temp_dict.py"

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
            page.screenshot(path="/output/screenshot.png")
            page_source = await page.content()
            html_content= await ascrape_playwright(page_source,info_data["info"]['marketplace'])#, tags)
            
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
            # extracted_content = main_dict_changes(**kwargs,
                                        # content=html_content)

            # if os.path.exists('/output/cache_approv.txt'):
            #     temp_file_dir = "/output/cache_approv.txt"
            # else: # else perform main dictionary
            extracted_content,lc = get_dictionary_for_product(lc, # local-page-level
                                                                info_data["info"]["asin"], # product-id
                                                                html_content, # content
                                                                **kwargs)

            pprint.pprint(extracted_content)
            print()
            print("-----------------------")

            # Loading Files
            # ==============================================================================
            # loading dictionary
            with open(temp_file_dir, 'r') as file:
                content = file.read()
                content = content.split('=', 1)[1].strip() #remove the 'data_dict =' parts
                data_dict = ast.literal_eval(content)
            # loading html content
            with open('/output/html_content.txt', 'r', encoding='utf-8') as file:
                page = file.read()
            soup = BeautifulSoup(page, 'html.parser')
            # ===============================================================================

            # Extracting Content
            # ==============================================================================
            data = extract_review_data(soup, data_dict)
            print()
            print("Printing of Data after Extraction")
            print("---------------------------------")
            print(data)
            print("---------------------------------")
            print()
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
            # review_titles = remove_duplicates(review_titles)
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

    await browser.close()
    

    # save overall output
    # ====================================================
    if lor:
        save_output(lor)
    else:
        print("Unable To Extract Content from Product")
    # ====================================================
# ====================================================================================



# Main Loop
# ========================================================

# Main User Prompt
country_code = os.getenv('COUNTRY_CODE')
# parser = argparse.ArgumentParser(description='Process country code.')
# parser.add_argument('--country_code', type=str, help='Enter country code (i.e, us, es, fr, it, etc)', required=True)
# args = parser.parse_args()
# cc = args.country_code.lower()
cc = country_code.lower()
print(f"Scraping {cc}")
# Dataframe Loading
# ========================================
df = get_googleSheet(f'{cc}') #by default us
amazon_links = df['Amazon page link']
asins = df['ASIN']
pdt_names = df['Product Name']
sku = df['SKU']
# ========================================

for base_url, asins, pdt_names, sku in zip(amazon_links, asins, pdt_names, sku):

    custom_headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/28.0.1500.52 Safari/537.36',
    }

    max_pages = 2
    page_count = 1
    lor = [] # list of reviews
    lc = {} #page specific cache

    info_data = {
        "info": {
            "marketplace": f"{cc}", # by default US
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
        page = requests.get(base_url,headers=custom_headers)
        if page.status_code == 200:
            print(f"Page is accessible for {base_url}")
            # assuming us is always chosen can modify later

            if cc == 'us':
                review_url = f"https://www.amazon.com/product-reviews/{asins}/ref=cm_cr_arp_d_viewopt_sr?ie=UTF8&filterByStar=all_stars&reviewerType=all_reviews&sortBy=recent&pageNumber={page_count}#reviews-filter-bar"
            else:
                review_url = f"https://www.amazon.{cc}/product-reviews/{asins}/ref=cm_cr_arp_d_viewopt_sr?ie=UTF8&filterByStar=all_stars&reviewerType=all_reviews&sortBy=recent&pageNumber={page_count}#reviews-filter-bar"
            
            # review_url = f"https://www.amazon.com/product-reviews/" + asins + f"?pageNumber={page_count}&sortBy=recent&formatType=current_format"
            print("Scraping from url: " + base_url)
            print(f"Entering URL - {review_url}")
            # review_url = "https://www.amazon.es/product-reviews/B08HM31MQP/ref=cm_cr_arp_d_viewopt_sr?ie=UTF8&filterByStar=all_stars&reviewerType=all_reviews&pageNumber=1#reviews-filter-bar"
            try:
                asyncio.run(scrape_with_playwright(
                    start_url = review_url,
                    info_data = info_data,
                    lor = lor,
                    lc=lc
                ))
            except Exception as e:
                print(f"An error was caught: {e}")
            page_count = page_count + 1
            time.sleep(30) # wait for 30 seconds
        else:
            print(f"Unable to access URL - {base_url}")
            time.sleep(30) # wait for 30 seconds

    break
# ========================================================