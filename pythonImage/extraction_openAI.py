# Libraries & Imports
# =================================================================
import os
import subprocess
import sys
from dotenv import load_dotenv
from langchain.chains import (create_extraction_chain,
                              create_extraction_chain_pydantic)
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain import OpenAI

openai_model = "gpt-4o-mini-2024-07-18" # can change to gpt-4 models
# current token limit
token_limit = 2000
# =================================================================

# Loading of API & Setting up of LLM
# =================================================================
load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(temperature=0, model=openai_model,
                 openai_api_key=openai_api_key, verbose=True, streaming=True,
                 max_tokens=token_limit)
# =================================================================



# Main Prompt 
# ======================================================================================================
chat_prompt = PromptTemplate(
    template = """
               You are a web scraping expert and you are able to identify common selectors used for extracting information.
               You will be provided a python dictionary that contains types of data we want to collect followed by their
               corresponding tag they belong to and which selector they fall under.
               Your main task is to change up the tags and selectors after studying the structure of the html content.

               ** Please refer to the example below for a better understanding: **

               raw html:
               ###
               <span id='23'>Reviewer Name</span>
               <span id="review-star-rating">5.0 out of 5 stars</span>
               <span id="review-star-rating">4.0 out of 5 stars</span>
               <a href="/gp/profile/amzn1.account.AFBV7XP2FAZDLG...">© 1996-2024, Amazon.com, Inc. or its affiliates</a>
               <a href="/gp/customer-reviews/R2DHJQG70ZXGV2/ref=cm_cr_arp_d_rv..."></a>
               <span id='review-date'>Reviewed in the United States on January 18, 2021</span>
               <span id='customer_review_foreign-R1I17YBKE584OK'>Reviewed in Mexico on Feb 11, 2021</span>
               <span id='review-date'>Reviewed in the United States on Feb 21, 2021</span>
               <span id="cmps-review-star-rating">4.0 out of 5 stars</span>
               ###

               dictionary:
               ###
               data_dict = (
                    'Reviewer Name': (
                        'tag': 'span',
                        'selector': ('id': '23')
                    ),
                    'Review Rating': (
                        'tag': 'span',
                        'selector': ('id': 'review-star-rating')
                    ),
                    'Reviewer Amazon Account': (
                        'tag': 'a',
                        'selector': ('href_contains':'/gp/profile/amzn1.account.')
                    ),
                    'Reviewer ID': (
                        'tag': 'a'
                        'selector': ('href_contains':'/gp/customer-reviews/')
                    ),
                    'Review Date': (
                        'tag': 'span',
                        'selector': ('id': 'review-date')
                    ),
                )
                ###

                ** FROM THE PREVIOUS EXAMPLE, ONE KEY OBSERVATION IS THE NEED TO UNDERSTAND THE SPECIFIC REQUIREMENTS FOR 'Review Date.' IT IS IMPORTANT TO ENSURE THAT WE CAPTURE ONLY VALID IDs, EXCLUDING ANY IDs THAT ARE OVERLY UNIQUE OR IRRELEVANT TO THE INTENDED FILTERING PROCESS. **
                ** FURTHERMOR, SIMILAR FOR 'Review Date', FOR 'Review Rating' THE SAME CONTEXT HAS TO BE FOLLOWED, STUDY THE HTML CAREFULLY. ** 

                in the dictionary, the 'id' may not always be an id, it may be a class, href_contains, or even a data-hook.
                ### YOUR JOB IS TO FIND THESE PATTERNS OR CHANGES AND UPDATE THE DICTIONARY!! ###

                Guidelines:
                1. STUDY THE HTML CAREFULLY.
                2. DO NOT MAKE ANY CHANGES TO THE DICTIONARY OTHER THAN WHAT YOUVE BEEN TOLD TO CHANGE.
                3. NO EXPLAINATIONS OR INSTRUCTIONS IS NEEDED.
                4. NO MARKDOWN FORMATTING IS NEEDED (NO TRIPLE BACKTICKS or MARKDOWN LANGUAGES)
                5. FOR AMAZON ACCOUNTS THEY USUALLY ARE IN THE FORM OF URLS
                6. YOU DO NOT NEED TO ADD ANY ADDITIONAL FIELDS. PLEASE ADHERE TO THE FORMAT AND STRUCTURE

                PLEASE STUDY THE HTML CONTENT AND UPDATE THE DICTIONARY ACCORDINGLY
                
                RAW HTML:
                ###
                {content}
                ###

                DICTIONARY:
                ###
                {dict}
                ###
    """,
    input_variables=['content','dict'],
)


chain = LLMChain(llm=llm, prompt=chat_prompt)
# ======================================================================================================


# Get Dictionary Generated from Bot (OpenAI)
# =================================================================
def get_dict_from_langchain(content: str, **kwargs):
    with open("/output/dict_structure.py", 'r') as file:
        dict = file.read()
    response = chain.run(content=content,dict=dict)
    return response.strip()
# =================================================================



# Bot Dictionary Generation
# =================================================================
def write_dict(dict):
    try:
        with open("/output/temp_dict.py", "w") as f: #outputting on file for debugging purposes
            f.write(dict)
            print("Dict Saved Successfully!!")
            return dict
    except Exception as e:
        results = f"Error: {e}"
        return results
# =================================================================



# Main Dictionary Function
# =================================================================
def main_dict_changes(content: str, **kwargs):
    print("Generating dict using LangChain...")
    dict_to_append = get_dict_from_langchain(content, **kwargs)
    print("Executing the dict...")
    dict_main = write_dict(dict_to_append)
    # print(dict_main)
    return dict_main
# =================================================================
