# env: .dockerSpiderEnv\Scripts\activate
# command to run docker: docker run --name dockerized_spider_8 -v C:\Polytechnic_web_crawler_with_docker:/output  data_collection_dker
# Libraries & Imports
# =================================================================
from playwright.async_api import async_playwright
from schemas import aws_review_schema as aws_rev
from extraction_openAI import extract
from extraction_openAI import get_googleSheet
from scrape import ascrape_playwright
import asyncio
import pprint
from bs4 import BeautifulSoup
import json
import os
import gzip
# =================================================================

# Dataframe Loading
# ========================================
df = get_googleSheet('us') #by default us
amazon_links = df['Amazon page link']
asins = df['ASIN']
pdt_names = df['Product Name']
sku = df['SKU']
# ========================================

async def scrape_with_playwright(start_url: str,info_data: dict, **kwargs):
    global num_calls
    list_of_reviews = []
    async with async_playwright() as p:

        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = start_url

        while True:
            await page.goto(url, wait_until='networkidle')
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
            
            # saving content as json
            # ==============================================================================
            cleaned_content = extracted_content.strip("()").strip("`").replace("json\n", "")
            # print(cleaned_content)
            reviews = json.loads(cleaned_content)

            for review in reviews:
                review_id = review["Reviewer's ID"]
                parts = review_id.split('-')
                review["Reviewer's ID"] = f"{parts[1]}"
                review["Customer Reivew Link"] = f"https://www.amazon.com/product-review/{parts[1]}"
                review['Reviewer Link'] = f"https://www.amazon.com{review['Reviewer Link'].rstrip('.')}"
                review['Info'] = info_data

            list_of_reviews.extend(reviews)
            # json_output = json.dumps(reviews, indent=4)

            # ==============================================================================
            break
            # Paginition (Works)
            # ==============================================================================
            async with async_playwright() as p:
                soup = BeautifulSoup(page_source, 'html.parser')
                next_button = soup.select_one('li.a-last a')
                print(next_button)
                if next_button and 'href' in next_button.attrs:
                    next_page_url = 'https://www.amazon.com' + next_button['href']
                    url = next_page_url 
                    print("URL PRINTING")
                    print("------------")
                    print(url)
                    print("------------")
                    time.sleep(30)
                else:
                    # No more pages to scrape, break the loop
                    print("No more pages to scrape.")
                    break
            # ==============================================================================

        await browser.close()

    # save overall output
    # ====================================================
    output_dir = "/output/amz-us-reviews" # by default us
    # output_dir = "C:\Polytechnic_web_crawler_with_docker"
    os.makedirs(output_dir, exist_ok=True)  # Create directory if it doesn't exist
    for index, review in enumerate(list_of_reviews):
        json_filename = os.path.join(output_dir, f"review_{index + 1}.json") #f"{review['Info']['asin']}_{index + 1}.json"
        gz_filename = os.path.join(output_dir, f"review_{index + 1}.json.gz")
        with open(json_filename, 'w', encoding='utf-8') as json_file:
            json.dump(review, json_file, indent=4)
        with open(json_filename, 'rb') as json_file:
            with gzip.open(gz_filename, 'wb') as gz_file:
                gz_file.writelines(json_file)
        os.remove(json_filename)
    # ====================================================


# Main Script
# ========================================================
for base_url, asins, pdt_names, sku in zip(amazon_links, asins, pdt_names, sku):
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
        start_url=review_url,
        info_data = info_data,
        # tags=["span", "a"],
        schema=aws_rev
    ))

    break
# ========================================================