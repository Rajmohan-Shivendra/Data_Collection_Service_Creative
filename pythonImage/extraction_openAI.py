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

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(temperature=0, model=openai_model,
                 openai_api_key=openai_api_key, verbose=True, streaming=True,
                 max_tokens=token_limit)


# chat prompt
# ======================================================================================================
# chat_prompt = PromptTemplate( 
#             template= """
#             Please extract the review content from the provided web content according to the following guidelines. Take your time to ensure all reviews are accurately extracted.

#             Guidelines:
#             1. Extract the following details for each review:
#             - Reviewer's ID (E.g, customer_review-R259E3F8KQB7K7)
#             - Reviewer's name
#             - Reviewer Link (Link to his/her Amazon Account)
#             - Rating (out of 5 stars)
#             - Review title (The title of the review)
#             - Review date
#             - Review description (The actual reviewer's inputs)
#             2. Duplicates: Be mindful of duplicate statements, especially in review descriptions. Ensure only one instance of each unique statement is extracted.
#             3. Please keep the extracted reviews the way they are, 
#                ###
#                DO NOT CREATE YOUR OWN INPUTS (IMPORTANT!!).
#                ###
#             4. 
#                 ###
#                 Please ensure that all relevant details are included without interruption.
#                 ###
#             5.
#                 ###
#                 ONLY TAKE REVIEWS REVIEWED IN THE UNITED STATES (US) IGNORE THE OTHER COUNTRIES
#                 ###
#             Format the extracted reviews as JSON. Here is the web content to analyze:
#             ###
#             {content}
#             ###
#             """,
#             input_variables=["content"],
#         )

# chat_prompt = PromptTemplate(
#             template= """ 
#             Please create a python script (.py) to
#             extract the review content from the provided web content (in HTML) according to the following guidelines. 
#             Take your time to ensure all reviews are accurately extracted.

#             Guidelines:
#              1. Extract the following details for each review:
#              - Reviewer's ID (E.g, customer_review-R259E3F8KQB7K7),
#              - Reviewer's name,
#              - Reviewer Link (Link to his/her Amazon Account),
#              - Rating (out of 5 stars),
#              - Review title (The title of the review),
#              - Review date,
#              - Review description (The actual reviewer's inputs).
#              2.The script you generate should only be used under the library "from bs4 import BeautifulSoup".
#              3.### ONLY TAKE REVIEWS REVIEWED IN THE UNITED STATES (US) IGNORE THE OTHER COUNTRIES! ###
             
#              Format the extracted reviews as JSON. Here is the web content (in HTML) to analyze:
#              ###
#              {content}
#              ###
#              """,
#              input_variables=["content"],
# )

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

# chat_prompt = PromptTemplate(
#     template = """
#                 Please write a Python script using the BeautifulSoup library to extract review data from the provided HTML content. Ensure that all reviews are accurately extracted according to the following specifications:

#                 ### Task Guidelines:
#                 1. Extract the following details for each review:
#                     - **Reviewer ID** (e.g., "customer_review-R259E3F8KQB7K7"),
#                     - **Reviewer Name**,
#                     - **Reviewer Profile Link** (URL to their Amazon account),
#                     - **Rating** (out of 5 stars),
#                     - **Review Title** (the headline of the review),
#                     - **Review Date**,
#                     - **Review Description** (the content of the review).

#                 2. **Only include reviews** that were written **in the United States (US)**. Disregard reviews from any other countries.

#                 3. The output should be **formatted as JSON**.

#                 4. Use the **BeautifulSoup library** to parse and extract data from the HTML content.

#                 5. **NO EXPLAINATIONS OR INSTRUCTIONS IS NEEDED** ### ONLY CODE ## **VERY IMPORTANT**.

#                 6. **The HTML content will be given to you in a .txt file (/output/html_content.txt) which should be passed to the script**. Do not generate or hard-code the HTML in the script itself.

#                 7. Generate Python code **without markdown formatting (no triple backticks or markdown language tags)**. ###Provide only plain Python code###.

#                 Format the extracted reviews as JSON and **output the extracted content as a .json file**. Here is the web content (in HTML) to analyze:
#                 ###
#                 {content}
#                 ###
#                 **Please take your time to understand the structure of the content, finding patterns to extract the data effectively**.
#                 Generate a Python script (.py file) based on these requirements.

#                 ** PLEASE DO READ UP THE SCRIPT TEMPLATE GUIDE AS IT CONTAINS INFO ABOUT THE EXTRACTION FOLLOW IT TO A TEE **
#                 ** PLEASE STUDY THE TAGS IN THE HTML CONTENT CAREFULLY DO NOT COME UP WITH YOUR OWN TAGS **
#                 ** DONT USE DIVS TO FIND TAGS **
#                 ###
#                 {script_template}
#                 ###

#     """,
#     input_variables=["content","script_template"],
# )

chain = LLMChain(llm=llm, prompt=chat_prompt)
# ======================================================================================================

def get_dict_from_langchain(content: str, **kwargs):
    with open("/output/dict_structure.py", 'r') as file:
        dict = file.read()
    response = chain.run(content=content,dict=dict)
    return response.strip()

def write_dict(dict):
    try:
        with open("/output/temp_dict.py", "w") as f: #outputting on file for debugging purposes
            f.write(dict)
            print("Dict Saved Successfully!!")
            return dict
    except Exception as e:
        results = f"Error: {e}"
        return results

def main_dict_changes(content: str, **kwargs):
    print("Generating dict using LangChain...")
    dict_to_append = get_dict_from_langchain(content, **kwargs)
    print("Executing the dict...")
    dict_main = write_dict(dict_to_append)
    # print(dict_main)
    return dict_main



# def get_code_from_langchain(content: str, **kwargs):
#     """
#     The `extract` function takes in a string `content` and additional keyword arguments, and returns the
#     extracted data based on the provided schema.
#     """
#     # script for openai to be of use to follow as a guide
#     with open("/output/script_structure.py", 'r') as file:
#         script_template = file.read()

#     response = chain.run(content=content,dict=dict, schema=kwargs["schema"])
#     return response.strip()

# def execute_code(code, timeout=10):
#     with open("/output/temp_code.py", "w") as f:
#         f.write(code)
#     try:
#         result = subprocess.run([sys.executable, "/output/temp_code.py"], capture_output=True, text=True, check=True, timeout=timeout)
#         print("No Error Received...")
#         print("Executed Sucessfully")
#         return result.stdout, False  # No error
#     except subprocess.CalledProcessError as e:
#         print("Error Received...")
#         return e.stdout + e.stderr, True  # There was an error
#     except subprocess.TimeoutExpired:
#         print("Execution Timed Out...")
#         return "Execution timed out.", True  # Execution timed out
    
# def run_extraction(content: str, **kwargs):
#     error_exists = True
#     retry_count = 0
#     max_retries = 2  # Retry a maximum of 2 times

#     while error_exists:
#         print("Generating code using LangChain...")
#         code = get_code_from_langchain(content, **kwargs)
#         print("Executing the code and checking for errors...")

#         output, error_exists = execute_code(code)
#         if error_exists:
#             print(f"Errors found on attempt {retry_count + 1}, output:\n", output)
#             with open("/output/temp_code.py", "r") as file:
#                 script = file.read()
#             new_content = f"The following script was generated by you: ###\n{script}\n### But the following error occurred: ###\n{output}\n### Please **fix the error**."
#             retry_count += 1
#             # Regenerate the code using the new prompt with the script and error
#             content = new_content
#         else:
#             print("Execution successful! Output:\n", output)
#             return output
        
#     if error_exists:
#         print(f"Max retries reached ({max_retries}). Still facing errors.")
#         return output  # Returning the last output after retries