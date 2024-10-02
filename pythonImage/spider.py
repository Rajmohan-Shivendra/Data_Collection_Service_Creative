# env: .dockerSpiderEnv\Scripts\activate
# command to run docker: docker run --name dockerized_spider_8 -v C:\Polytechnic_web_crawler_with_docker:/output  data_collection_dker
# Libraries & Imports
# =================================================================
from playwright.async_api import async_playwright
from schemas import aws_review_schema as aws_rev
from extraction_openAI import extract
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
    max_retries = 3
    retries = 0

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
            extracted_content = extract(**kwargs,
                                        content=html_content)
            pprint.pprint(extracted_content)
            print()
            print("-----------------------")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break  # Break the loop on unexpected errors

    print("Max retries reached. Could not process the content.")
    return None  # Return None or handle the failure case as needed
# ========================================

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
            extracted_content = extract(**kwargs,
                                        content=html_content)
            pprint.pprint(extracted_content)
            print()
            print("-----------------------")
            # break
            
            # Cleaning Content
            # ==============================================================================
            reviews = data_cleaning(extracted_content, html_content, **kwargs)

            if reviews != None:
                for review in reviews:
                    review_id = review["Reviewer's ID"]
                    parts = review_id.split('-')
                    review["Reviewer's ID"] = f"{parts[1]}"
                    review["Customer Reivew Link"] = f"https://www.amazon.com/product-review/{parts[1]}"
                    review['Reviewer Link'] = f"https://www.amazon.com{review['Reviewer Link'].rstrip('.')}"
                    review['Info'] = info_data

                lor.extend(reviews)
            else:
                pass #move on to paginition, will skip review of this page

            # ==============================================================================
            # Paginition (Works)
            # ==============================================================================
            async with async_playwright() as p:

                # Variables for Paginiton
                # =======================
                max_pages = 3
                page_count = 1
                # =======================

                soup = BeautifulSoup(page_source, 'html.parser')
                next_button = soup.select_one('li.a-last a')
                print(next_button)
                if page_count > max_pages:
                    # limit to only scrape a maximum of 3 pages per product
                    print("Max 3 Pages Scraped")
                    break
                else:
                    if next_button and 'href' in next_button.attrs:
                        next_page_url = 'https://www.amazon.com' + next_button['href']
                        url = next_page_url 
                        print("URL PRINTING")
                        print("------------")
                        print(url)
                        print("------------")
                        time.sleep(30)
                        page_count = page_count + 1
                    else:
                        # No more pages to scrape, break the loop
                        print("No more pages to scrape.")
                        break
            # ==============================================================================

        await browser.close()

    # save overall output
    # ====================================================
    if not lor:
        save_output(lor)
    else:
        print("Unable To Extract Content from Product")
    # ====================================================

# Main Script
# ========================================================
for base_url, asins, pdt_names, sku in zip(amazon_links, asins, pdt_names, sku):
    lor = [] # list of reviews

    # base_url can be used for product scarping (pdt_url)
    # assuming us is always chosen can modify later
    review_url = "https://www.amazon.com/product-reviews/" + asins + "?pageNumber=1&sortBy=recent&formatType=current_format"
    print("Scraping from url: " + base_url)

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

    asyncio.run(scrape_with_playwright(
        start_url = review_url,
        info_data = info_data,
        lor = lor,
        schema=aws_rev
    ))

    break
# ========================================================