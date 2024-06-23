from typing import Optional, Type
from pydantic.v1 import BaseModel, BaseSettings, Field
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain.agents import tool
from langchain_community.tools.human import HumanInputRun
import pandas as pd
from pytrends.request import TrendReq
from dotenv import load_dotenv
from langchain.tools import BaseTool, StructuredTool, tool
from serpapi import GoogleSearch

def get_input() -> str:
    print("Insert your text. Enter 'q' or press Ctrl-D (or Ctrl-Z on Windows) to end.")
    contents = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == "q":
            break
        contents.append(line)
    return "\n".join(contents)

human_tool = HumanInputRun(input_func=get_input)


load_dotenv()

serp_api_key = ""

class GoogleTrendsInput(BaseModel):
    input: str = Field(description='A JSON string containing the search term(s) to analyze trends for (as "query"), the time range (as "timeframe", default is past 3 months), and optionally the geographic location (as "geo", default is worldwide). Example: {"query": "artificial intelligence, machine learning", "timeframe": "today 12-m", "geo": "US"}')

@tool("google_trends", args_schema=GoogleTrendsInput)
def google_trends(query: str, timeframe: str = "today 3-m",) -> str:
        """A custom tool that integrates with the Google Trends API to fetch data on potential key phrases, handle API requests, and process the response data in a structured format for analysis."""
        params1 = {
        "engine": "google_trends",
        "q": query,
        "date": timeframe,
        "tz": "420",
        "data_type": "TIMESERIES",
        "api_key": serp_api_key
        }

        params2 = {
        "engine": "google_trends",
        "q": query,
        "data_type": "RELATED_QUERIES",
        "api_key": "787635eb77da4daf42e7253408e4cf68fc878805f403eb41685dbb16dcbc34ff"
        }

        search = GoogleSearch(params1)
        results = search.get_dict()
        if "interest_over_time" in results:
            interest_over_time = results["interest_over_time"]
        else:
            interest_over_time = "{}"

        search = GoogleSearch(params2)
        results = search.get_dict()
        try:
            related_queries = results["related_queries"]
        except:
            related_queries = "{}"

        result = {
            "interest_over_time":interest_over_time,
            # "interest_by_region": interest_by_region_df.to_dict(),
            "related_queries": related_queries
        }

        return result


from typing import Type 
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import re
import json

class KeywordCheckInput(BaseModel):
    input: str = Field(description='A JSON string containing the text to analyze for keyword frequency and density, and the keyword to check. Example: {"text": "This is an example text about keyword density. Keyword density is important for SEO. Make sure your keyword density is not too high or too low.", "keyword": "keyword density"}')

@tool("seo_keyword_check", args_schema=KeywordCheckInput, return_direct=False)
def seo_keyword_check(input: str) -> str:
    """Check the frequency and density of a keyword in the given text."""
    input_data = json.loads(input)
    text = input_data['text']
    keyword = input_data['keyword']

    text = re.sub(r'[^\w\s]', '', text.lower())
    
    total_words = len(text.split())
    
    keyword_freq = len(re.findall(r'\b' + re.escape(keyword.lower()) + r'\b', text))
    
    keyword_density = round((keyword_freq / total_words) * 100, 2) if total_words > 0 else 0

    return f"Keyword '{keyword}' appears {keyword_freq} times. Keyword density is {keyword_density}%."
