from typing import Optional, Type
from pydantic.v1 import BaseModel, BaseSettings, Field
from langchain.agents import tool
from playwright.sync_api import sync_playwright
import json
import schedule

class LinkedInInput(BaseModel):
    input: str = Field(description="The action to perform on LinkedIn and associated data. Example: {\"action\": \"login\", \"username\": \"user@company.com\", \"password\": \"abc123\"}")

@tool("linkedin_browser", args_schema=LinkedInInput, return_direct=False)
def linkedin_browser(input: str) -> str:
    """Automate LinkedIn interactions in a browser like login, navigate, get posts, publish post."""
    input_data = json.loads(input)
    action = input_data["action"].lower()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        if action == "login":
            page.goto("https://www.linkedin.com/login")
            page.fill("input[name='session_key']", input_data["username"])
            page.fill("input[name='session_password']", input_data["password"])
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            browser.close()
            return "Logged in to LinkedIn successfully"
        
        elif action == "navigate":
            page.goto(input_data["url"])
            page.wait_for_load_state("networkidle") 
            browser.close()
            return f"Navigated to {input_data['url']} successfully"

        elif action == "get_posts":
            page.goto("https://www.linkedin.com/feed/")
            
            posts = []
            has_more = True
            while has_more:
                post_elements = page.query_selector_all(".feed-shared-update-v2")
                for post in post_elements:
                    try:
                        text = post.query_selector(".feed-shared-text").inner_text()
                        author = post.query_selector(".feed-shared-actor__name").inner_text()
                        timestamp = post.query_selector(".feed-shared-actor__sub-description").inner_text()
                        posts.append({"text": text, "author": author, "timestamp": timestamp})
                    except:
                        pass
                
                has_more = page.query_selector(".artdeco-pagination__button--next") is not None
                if has_more:
                    page.click(".artdeco-pagination__button--next")
                    page.wait_for_load_state("networkidle")

            browser.close()  
            return json.dumps(posts)

        elif action == "publish_post":
            page.goto("https://www.linkedin.com/post/new/")
            page.fill(".ql-editor", input_data["text"])
            page.click(".share-actions__primary-action")
            page.wait_for_selector(".feed-shared-update-v2")
            post_url = page.url
            browser.close()
            return f"Published post on LinkedIn successfully. Post URL: {post_url}"

        else:
            browser.close()
            return f"Unsupported LinkedIn action: {action}"


from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import json

class PostFilterInput(BaseModel):
    input: str = Field(description="JSON string of LinkedIn post data to filter by likes, comments, keywords, companies. Example: {\"posts\": [{\"id\": \"123\", \"text\": \"Post 1\", \"likes\": 10, \"comments\": 5, \"company\": \"Acme\"}, {\"id\": \"456\", \"text\": \"Post 2\", \"likes\": 50, \"comments\": 20, \"company\": \"Other\"}], \"min_likes\": 20, \"min_comments\": 5, \"keywords\": [\"AI\", \"ML\"], \"companies\": [\"Acme\", \"AI Corp\"]}")

@tool("linkedin_post_filter", args_schema=PostFilterInput, return_direct=False)
def linkedin_post_filter(input: str) -> str:
    """Filter LinkedIn posts by min likes, comments, keywords, company."""
    
    input_data = json.loads(input)
    posts = input_data["posts"]
    min_likes = input_data["min_likes"]
    min_comments = input_data["min_comments"]
    keywords = input_data["keywords"] 
    companies = input_data["companies"]

    filtered_posts = [
        post for post in posts
        if post['likes'] >= min_likes
        and post['comments'] >= min_comments
        and any(keyword.lower() in post['text'].lower() for keyword in keywords)
        and post['company'] in companies
    ]

    return json.dumps(filtered_posts)


import json
from typing import Optional, Type
from pydantic.v1 import BaseModel, BaseSettings, Field
from langchain.agents import tool
from langchain.tools import HumanInputRun

class ApprovalInput(BaseModel):
    input: str = Field(description="The post/comment to review. Example: {\"content\": \"Example post\", \"source\": \"https://example.com/123\", \"author\": \"user\"}")

@tool("human_approval", args_schema=ApprovalInput, return_direct=False)
def human_approval(input: str) -> str:
    """Request human approval for a post/comment. Records the decision."""
    input_data = ApprovalInput.parse_raw(input)
    input_dict = json.loads(input_data.input)
    
    content = input_dict["content"]
    source = input_dict["source"]
    author = input_dict["author"]
    
    print(f"Please review:\nContent: {content}\nSource: {source}\nAuthor: {author}")
    
    human_input = HumanInputRun(input_data.input)
    
    if "approve" in human_input.lower():
        approval_record = {
            "content": content,
            "source": source,
            "author": author,
            "decision": "approved"
        }
        with open("approval_records.json", "a") as file:
            json.dump(approval_record, file)
            file.write("\n")
        
        return "Post/comment approved"
    else:
        rejection_record = {
            "content": content,
            "source": source,
            "author": author,
            "decision": "rejected"
        }
        with open("rejection_records.json", "a") as file:
            json.dump(rejection_record, file)
            file.write("\n")
        
        return "Post/comment rejected"


from typing import List, Dict
from datetime import datetime, timedelta
import json
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import schedule

class ScheduleInput(BaseModel):
    input: str = Field(description="JSON list of posts with content, target, importance, urgency. Example: '[{\"content\": \"Great post!\", \"target\": \"https://example.com/123\", \"importance\": 4, \"urgency\": 3}, {\"content\": \"Thanks for sharing\", \"target\": \"https://example.com/456\", \"importance\": 3, \"urgency\": 2}]'")

scheduled_jobs = []

def get_optimal_time(post: Dict) -> datetime:
    """Determine optimal posting time based on importance and urgency"""
    importance = post['importance']
    urgency = post['urgency']
    
    base_delay = 24
    importance_multiplier = 1.5
    urgency_multiplier = 2
    hours_delay = max(1, base_delay - (importance * importance_multiplier) - (urgency * urgency_multiplier))
    return datetime.now() + timedelta(hours=hours_delay)

def post_job(post: Dict):
    print(f"Posting {post['content']} to {post['target']}")

@tool("schedule_posts", args_schema=ScheduleInput, return_direct=False)
def schedule_posts(input: str) -> str:
    """Schedule posts at optimal times based on importance, urgency, engagement."""
    posts_data = json.loads(input)
    
    sorted_posts = sorted(posts_data, key=lambda post: (post['importance'], post['urgency']), reverse=True)
    
    for post in sorted_posts:
        post_time = get_optimal_time(post)
        job = schedule.every().day.at(post_time.strftime("%H:%M")).do(post_job, post)
        scheduled_jobs.append(job)

    num_posts = len(sorted_posts)
    return f"Scheduled {num_posts} post(s) optimally based on priority."


from typing import Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import re
from langchain.utilities import GoogleSerperAPIWrapper

class GoogleSerperAPIWrapperWithAPIKey(GoogleSerperAPIWrapper):
    def __init__(self, serper_api_key: str, k: int = 10):
        super().__init__(serper_api_key=serper_api_key, k=k)

search = GoogleSerperAPIWrapperWithAPIKey(serper_api_key="YOUR_SERPER_API_KEY")

class LinkedInPostInput(BaseModel):
    input: str = Field(description="LinkedIn post URL to monitor. Example: {\"post_url\": \"https://www.linkedin.com/posts/user_id\"}")

@tool("monitor_linkedin_post", args_schema=LinkedInPostInput, return_direct=False)
def monitor_linkedin_post(input: str) -> str:
    """Monitor a LinkedIn post's views, likes, shares metrics."""
    
    input_data = LinkedInPostInput.parse_raw(input)
    post_url = input_data.input["post_url"]
    
    search_query = f"{post_url} linkedin post views likes shares"
    search_results = search.results(search_query)
    
    metrics = {}
    for result in search_results:
        views_match = re.search(r"(\d+) views", result["snippet"])
        if views_match:
            metrics["views"] = int(views_match.group(1))
        
        likes_match = re.search(r"(\d+) likes", result["snippet"]) 
        if likes_match:
            metrics["likes"] = int(likes_match.group(1))

        shares_match = re.search(r"(\d+) shares", result["snippet"])
        if shares_match:  
            metrics["shares"] = int(shares_match.group(1))

    if not metrics:
        return "Could not find metrics for the specified post."
    
    report = f"LinkedIn Post Metrics\nURL: {post_url}\nViews: {metrics.get('views', 'N/A')}\nLikes: {metrics.get('likes', 'N/A')}\nShares: {metrics.get('shares', 'N/A')}"
    
    return report

class AlertInput(BaseModel):
    input: str = Field(description="LinkedIn post URL and % change threshold to monitor. Example: {\"post_url\": \"https://www.linkedin.com/posts/user_id\", \"change_threshold\": 20}")
    
@tool("alert_post_changes", args_schema=AlertInput, return_direct=False)
def alert_post_changes(input: str) -> str:
    """Monitor a post and alert if metrics change above a threshold."""
    
    input_data = AlertInput.parse_raw(input)
    post_url = input_data.input["post_url"] 
    change_threshold = input_data.input["change_threshold"]
    
    initial_metrics_str = monitor_linkedin_post(input)
    initial_metrics = parse_metrics(initial_metrics_str)
    
    import time
    time.sleep(3600) # Check after 1 hour
    
    new_metrics_str = monitor_linkedin_post(input)
    new_metrics = parse_metrics(new_metrics_str)
    
    alert_messages = []
    for metric, initial_value in initial_metrics.items():
        new_value = new_metrics.get(metric, 0)
        if new_value >= initial_value * (1 + change_threshold/100):
            alert_messages.append(f"{metric.capitalize()} increased by {round(new_value/initial_value*100-100, 1)}% from {initial_value:,} to {new_value:,}")
        elif new_value <= initial_value * (1 - change_threshold/100):
            alert_messages.append(f"{metric.capitalize()} decreased by {round(100-new_value/initial_value*100, 1)}% from {initial_value:,} to {new_value:,}")
            
    if alert_messages:
        alert = f"Alert: Post metrics changed >{change_threshold}%\n\n" + "\n".join(alert_messages)
    else:
        alert = f"No metric changes >{change_threshold}% detected."
    
    return alert

def parse_metrics(metrics_str):
    metrics = {}
    for line in metrics_str.split("\n"):
        if ":" in line:
            metric, value = line.split(":")
            metrics[metric.lower()] = int(value.strip().replace(",",""))
    return metrics
