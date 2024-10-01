# Libraries & Imports
# =================================================================
import os
from dotenv import load_dotenv
from langchain.chains import (create_extraction_chain,
                              create_extraction_chain_pydantic)
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

openai_model = "gpt-4o-mini-2024-07-18" # can change to gpt-4 models
# current token limit
token_limit = 1800
# =================================================================

load_dotenv()
openai_api_key = os.getenv('OPENAI_API_KEY')
llm = ChatOpenAI(temperature=0, model=openai_model,
                 openai_api_key=openai_api_key, verbose=True, streaming=True,
                 max_tokens=token_limit)


# chat prompt
# ======================================================================================================
chat_prompt = PromptTemplate( 
            template= """
            Please extract the review content from the provided web content according to the following guidelines. Take your time to ensure all reviews are accurately extracted.

            Guidelines:
            1. Extract the following details for each review:
            - Reviewer's ID (E.g, customer_review-R259E3F8KQB7K7)
            - Reviewer's name
            - Reviewer Link (Link to his/her Amazon Account)
            - Rating (out of 5 stars)
            - Review title (The title of the review)
            - Review date
            - Review description (The actual reviewer's inputs)
            2. Duplicates: Be mindful of duplicate statements, especially in review descriptions. Ensure only one instance of each unique statement is extracted.
            3. Please keep the extracted reviews the way they are, 
               ###
               DO NOT CREATE YOUR OWN INPUTS (IMPORTANT!!).
               ###
            Format the extracted reviews as JSON. Here is the web content to analyze:
            ###
            {content}
            ###
            """,
            input_variables=["content"],
        )
chain = LLMChain(llm=llm, prompt=chat_prompt)
# ======================================================================================================


def extract(content: str, **kwargs):
    """
    The `extract` function takes in a string `content` and additional keyword arguments, and returns the
    extracted data based on the provided schema.
    """
    response = chain.run(content=content, schema=kwargs["schema"])
    return response

