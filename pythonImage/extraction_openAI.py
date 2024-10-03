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

chat_prompt = PromptTemplate(
            template= """ 
            Please create a python script (.py) to
            extract the review content from the provided web content (in HTML) according to the following guidelines. 
            Take your time to ensure all reviews are accurately extracted.

            Guidelines:
             1. Extract the following details for each review:
             - Reviewer's ID (E.g, customer_review-R259E3F8KQB7K7),
             - Reviewer's name,
             - Reviewer Link (Link to his/her Amazon Account),
             - Rating (out of 5 stars),
             - Review title (The title of the review),
             - Review date,
             - Review description (The actual reviewer's inputs).
             2.The script you generate should only be used under the library "from bs4 import BeautifulSoup".
             3.### ONLY TAKE REVIEWS REVIEWED IN THE UNITED STATES (US) IGNORE THE OTHER COUNTRIES! ###
             
             Format the extracted reviews as JSON. Here is the web content (in HTML) to analyze:
             ###
             {content}
             ###
             """,
             input_variables=["content"],
)

chain = LLMChain(llm=llm, prompt=chat_prompt)
# ======================================================================================================


def get_code_from_langchain(content: str, **kwargs):
    """
    The `extract` function takes in a string `content` and additional keyword arguments, and returns the
    extracted data based on the provided schema.
    """
    response = chain.run(content=content, schema=kwargs["schema"])
    return response.strip()

def execute_code(code, timeout=10):
    with open("/output/temp_code.py", "w") as f:
        f.write(code)

    try:
        result = subprocess.run([sys.executable, "temp_code.py"], capture_output=True, text=True, check=True, timeout=timeout)
        return result.stdout, False  # No error
    except subprocess.CalledProcessError as e:
        return e.stdout + e.stderr, True  # There was an error
    except subprocess.TimeoutExpired:
        return "Execution timed out.", True  # Execution timed out
    
def run_extraction(content: str, **kwargs):
    error_exists = True

    while error_exists:
        print("Generating code using LangChain...")
        # Generate code using LangChain
        code = get_code_from_langchain(content, **kwargs)
        print("Executing the code and checking for errors...")

        # Execute the code and capture the output
        output, error_exists = execute_code(code)
        if error_exists:
            print("Errors found, output:\n", output)
            # Optionally, implement logic to fix the errors here
        else:
            print("Execution successful! Output:\n", output)
            return output