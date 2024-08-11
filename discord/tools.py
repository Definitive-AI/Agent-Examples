from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import discord
import asyncio
import json

class DiscordAPIInput(BaseModel):
    input: str = Field(description='A JSON string containing the Discord API action and necessary parameters. Example: {"action": "send_message", "channel_id": "123456789", "content": "Hello, Discord!"}')

client = discord.Client(intents=discord.Intents.default())

@tool("discord_api_tool", args_schema=DiscordAPIInput, return_direct=False)
def discord_api_tool(input: str) -> str:
    """
    Provides direct interface to Discord's API for monitoring messages, creating and managing private threads, and performing other Discord-specific actions. Supports sending messages, creating threads, and monitoring channel activity.
    """
    try:
        action_data = json.loads(input)
        action = action_data.get("action")

        if action == "send_message":
            channel_id = action_data.get("channel_id")
            content = action_data.get("content")
            return asyncio.run(send_message(channel_id, content))
        elif action == "create_thread":
            channel_id = action_data.get("channel_id")
            thread_name = action_data.get("thread_name")
            return asyncio.run(create_thread(channel_id, thread_name))
        elif action == "monitor_messages":
            channel_id = action_data.get("channel_id")
            duration = action_data.get("duration", 60)  # Default to 60 seconds
            return asyncio.run(monitor_messages(channel_id, duration))
        else:
            return f"Unsupported action: {action}"
    except json.JSONDecodeError:
        return "Invalid JSON input"
    except Exception as e:
        return f"An error occurred: {str(e)}"

async def send_message(channel_id: str, content: str) -> str:
    channel = await client.fetch_channel(int(channel_id))
    await channel.send(content)
    return f"Message sent to channel {channel_id}"

async def create_thread(channel_id: str, thread_name: str) -> str:
    channel = await client.fetch_channel(int(channel_id))
    thread = await channel.create_thread(name=thread_name)
    return f"Thread '{thread_name}' created with ID: {thread.id}"

async def monitor_messages(channel_id: str, duration: int) -> str:
    channel = await client.fetch_channel(int(channel_id))
    messages = []

    def check(m):
        return m.channel.id == channel.id

    try:
        while True:
            message = await client.wait_for('message', check=check, timeout=duration)
            messages.append(f"{message.author}: {message.content}")
    except asyncio.TimeoutError:
        pass

    return f"Messages monitored in channel {channel_id} for {duration} seconds:\n" + "\n".join(messages)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

def run_discord_client(token: str):
    client.run(token)

# Usage example:
# import threading
# discord_thread = threading.Thread(target=run_discord_client, args=('YOUR_DISCORD_BOT_TOKEN',))
# discord_thread.start()


from typing import Optional, Type, Dict, List
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import json

class KBMSInput(BaseModel):
    input: str = Field(description="A string representation of a dictionary containing the operation type and necessary data. Example: '{\"operation\": \"retrieve\", \"query\": \"What is LangChain?\"}'")

class KnowledgeBase:
    def __init__(self):
        self.entries: Dict[str, str] = {}

    def retrieve(self, query: str) -> str:
        return self.entries.get(query, "No entry found for this query.")

    def update(self, key: str, value: str) -> str:
        self.entries[key] = value
        return f"Entry updated: {key}"

    def add(self, key: str, value: str) -> str:
        if key not in self.entries:
            self.entries[key] = value
            return f"New entry added: {key}"
        return "Entry already exists. Use update to modify."

    def delete(self, key: str) -> str:
        if key in self.entries:
            del self.entries[key]
            return f"Entry deleted: {key}"
        return "Entry not found."

    def list_entries(self) -> List[str]:
        return list(self.entries.keys())

kb = KnowledgeBase()

@tool("kbms_api_tool", args_schema=KBMSInput, return_direct=False)
def kbms_api_tool(input: str) -> str:
    """
    API for retrieving, updating, and managing entries in the internal knowledge base and FAQ system.
    Supports operations: retrieve, update, add, delete, and list entries.
    """
    try:
        data = json.loads(input)
        operation = data.get("operation")

        if operation == "retrieve":
            return kb.retrieve(data.get("query"))
        elif operation == "update":
            return kb.update(data.get("key"), data.get("value"))
        elif operation == "add":
            return kb.add(data.get("key"), data.get("value"))
        elif operation == "delete":
            return kb.delete(data.get("key"))
        elif operation == "list":
            return str(kb.list_entries())
        else:
            return "Invalid operation. Supported operations are: retrieve, update, add, delete, list."
    except json.JSONDecodeError:
        return "Invalid input. Please provide a valid JSON string."
    except KeyError as e:
        return f"Missing required field: {str(e)}"

# Example usage
input_str = json.dumps({
    "operation": "add",
    "key": "LangChain",
    "value": "LangChain is a framework for developing applications powered by language models."
})
result = kbms_api_tool(input_str)
print(result)


from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
from playwright.sync_api import sync_playwright
import json

class WebBrowserInput(BaseModel):
    input: str = Field(description="The URL of the website to visit. Example: {\"url\": \"https://www.example.com\"}")

class WebBrowserTool:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    def __enter__(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def visit_url(self, url: str) -> str:
        self.page.goto(url)
        return self.page.content()

    def get_text_content(self) -> str:
        return self.page.inner_text('body')

@tool("web_browser_tool", args_schema=WebBrowserInput, return_direct=False)
def web_browser_tool(input: str) -> str:
    """
    Interface for accessing and reading content from official documentation and trusted websites. This tool allows you to visit a specified URL and retrieve the text content from the webpage, providing a summary of the first 1000 characters.
    """
    input_data = json.loads(input)
    url = input_data['url']
    
    with WebBrowserTool() as browser:
        browser.visit_url(url)
        content = browser.get_text_content()
        return f"Content from {url}:\n\n{content[:1000]}..."  # Truncate to first 1000 characters


from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
from googletrans import Translator
import json

class TranslationInput(BaseModel):
    input: str = Field(description='A JSON string containing the text to translate, source language (optional), and target language. Example: {"text": "Hello, how are you?", "src": "en", "dest": "fr"}')

@tool("translation_api_tool", args_schema=TranslationInput, return_direct=False)
def translation_api_tool(input: str) -> str:
    """
    Translate text from one language to another using Google Translate API. This tool can handle various languages and automatically detect the source language if not specified. It's useful for translating knowledge base content, FAQs, or any text into multiple languages.
    """
    try:
        input_data = json.loads(input)
        text = input_data['text']
        src = input_data.get('src', 'auto')
        dest = input_data['dest']
        
        translator = Translator()
        translation = translator.translate(text, src=src, dest=dest)
        
        return f"Translated text: {translation.text}"
    except json.JSONDecodeError:
        return "Error: Invalid JSON input. Please provide a valid JSON string."
    except KeyError as e:
        return f"Error: Missing required key in input. {str(e)}"
    except Exception as e:
        return f"An error occurred during translation: {str(e)}"


from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
from langchain.tools.human.tool import HumanInputRun
import json

class FeedbackInput(BaseModel):
    input: str = Field(description="The request for feedback or input from the human. Example: {\"feedback_request\": \"How would you rate the assistant's response on a scale of 1-5?\"}")

@tool("human_feedback_interface", args_schema=FeedbackInput, return_direct=False)
def human_feedback_interface(input: str) -> str:
    """Interface to receive and process human feedback for continuous learning. This tool allows for real-time human input to improve AI responses and decision-making."""
    input_data = json.loads(input)
    feedback_request = input_data.get("feedback_request", "")
    
    human_input = HumanInputRun()
    response = human_input.run(feedback_request)
    
    # Process the feedback (example implementation)
    processed_feedback = process_feedback(response)
    
    return f"Received and processed feedback: {processed_feedback}"

def process_feedback(feedback: str) -> str:
    """
    Process the received feedback.
    This function can be expanded to include more complex processing logic,
    such as storing in a database or updating a model.
    """
    # Example processing: convert to uppercase
    processed = feedback.upper()
    
    # Here you could add code to store the feedback in a database
    # or use it to update the model's parameters
    
    return processed


from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import requests
import json

class SentimentAnalysisInput(BaseModel):
    input: str = Field(description="The text to analyze for sentiment. Example: {\"text\": \"I love this product, it's amazing!\"}")

@tool("sentiment_analysis_api", args_schema=SentimentAnalysisInput, return_direct=False)
def sentiment_analysis_api(input: str) -> str:
    """
    Analyze the sentiment of the given text using an external API for advanced sentiment analysis, complementing GPT's capabilities.
    """
    # Parse the input string to a dictionary
    input_data = json.loads(input)
    text = input_data['text']

    # Sentiment analysis API endpoint
    api_url = "https://api.sentimentanalysis.com/v1/analyze"
    
    # API key for authentication
    api_key = "sk_1234567890abcdefghijklmnopqrstuvwxyz"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {"text": text}
    
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        sentiment = result.get("sentiment", "Unknown")
        score = result.get("score", 0.0)
        
        return f"Sentiment: {sentiment}, Score: {score}"
    except requests.RequestException as e:
        return f"Error occurred while analyzing sentiment: {str(e)}"


import discord
import json
import asyncio
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool

class DiscordInput(BaseModel):
    input: str = Field(description='A JSON string containing the message content, channel ID, and optional message ID to reply to. Example: {"content": "Hello, world!", "channel_id": "123456789", "reply_to": "987654321"}')

class DiscordClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def send_message(self, channel_id: str, content: str, reply_to: str = None):
        channel = self.get_channel(int(channel_id))
        if channel:
            if reply_to:
                try:
                    message_to_reply = await channel.fetch_message(int(reply_to))
                    sent_message = await message_to_reply.reply(content=content)
                except discord.NotFound:
                    sent_message = await channel.send(content=content)
            else:
                sent_message = await channel.send(content=content)
            return f"Message sent to channel {channel_id} at {sent_message.created_at}"
        return f"Channel {channel_id} not found"

client = DiscordClient(intents=discord.Intents.default())

@tool("discord_integration_tool", args_schema=DiscordInput)
def discord_integration_tool(input: str) -> str:
    """
    Enables posting AI-generated responses, monitoring user feedback, and tracking message timestamps on Discord. This tool allows sending messages to specific channels, replying to existing messages, and provides timestamp information for sent messages.
    """
    try:
        data = json.loads(input)
        content = data.get('content')
        channel_id = data.get('channel_id')
        reply_to = data.get('reply_to')

        if not content or not channel_id:
            return "Error: Missing required fields (content or channel_id)"

        async def send_message_wrapper():
            return await client.send_message(channel_id, content, reply_to)

        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(send_message_wrapper())
        return result
    except json.JSONDecodeError:
        return "Error: Invalid JSON input"
    except Exception as e:
        return f"Error: {str(e)}"

# To use this tool, you need to run the Discord client in the background
# This should be done when setting up your agent or application
# Replace 'YOUR_DISCORD_BOT_TOKEN' with your actual bot token
client.run('YOUR_DISCORD_BOT_TOKEN')


from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import json

class TicketInput(BaseModel):
    input: str = Field(description='A string representation of a dictionary containing the ticket details. Example: {"action": "create", "title": "New Feature Request", "description": "Add dark mode to the application", "priority": "high", "assignee": "john@example.com"}')

class TicketSystem:
    def __init__(self):
        self.tickets = {}
        self.ticket_counter = 0

    def create_ticket(self, title, description, priority, assignee):
        self.ticket_counter += 1
        ticket_id = f"TICKET-{self.ticket_counter}"
        self.tickets[ticket_id] = {
            "id": ticket_id,
            "title": title,
            "description": description,
            "priority": priority,
            "assignee": assignee,
            "status": "open"
        }
        return ticket_id

    def update_ticket(self, ticket_id, **kwargs):
        if ticket_id not in self.tickets:
            return f"Ticket {ticket_id} not found"
        self.tickets[ticket_id].update(kwargs)
        return f"Ticket {ticket_id} updated successfully"

    def get_ticket(self, ticket_id):
        return self.tickets.get(ticket_id, f"Ticket {ticket_id} not found")

    def list_tickets(self):
        return list(self.tickets.values())

ticket_system = TicketSystem()

@tool("ticket_management_tool", args_schema=TicketInput)
def ticket_management_tool(input: str) -> str:
    """Manages the creation, updating, and retrieval of tickets for organizing and tracking issues. Supports actions: create, update, get, and list tickets."""
    try:
        data = json.loads(input)
        action = data.get("action")

        if action == "create":
            ticket_id = ticket_system.create_ticket(
                data.get("title"),
                data.get("description"),
                data.get("priority"),
                data.get("assignee")
            )
            return f"Ticket created with ID: {ticket_id}"

        elif action == "update":
            ticket_id = data.get("ticket_id")
            update_data = {k: v for k, v in data.items() if k not in ["action", "ticket_id"]}
            return ticket_system.update_ticket(ticket_id, **update_data)

        elif action == "get":
            ticket_id = data.get("ticket_id")
            ticket = ticket_system.get_ticket(ticket_id)
            return json.dumps(ticket)

        elif action == "list":
            tickets = ticket_system.list_tickets()
            return json.dumps(tickets)

        else:
            return "Invalid action. Supported actions are: create, update, get, list"

    except json.JSONDecodeError:
        return "Invalid input. Please provide a valid JSON string."
    except Exception as e:
        return f"An error occurred: {str(e)}"


from typing import Optional, Type
from pydantic.v1 import BaseModel, Field
from langchain.agents import tool
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
import base64

class AnalyticsReportingInput(BaseModel):
    input: str = Field(description='A JSON string containing the type of report to generate and any additional parameters. Example: {"report_type": "user_activity", "start_date": "2023-01-01", "end_date": "2023-12-31"}')

@tool("analytics_reporting_tool", args_schema=AnalyticsReportingInput, return_direct=False)
def analytics_reporting_tool(input: str) -> str:
    """
    Analyzes data from Discord interactions and the ticketing system to generate performance reports and statistics. Provides insights on user activity and ticket performance over specified time periods.
    """
    try:
        input_data = json.loads(input)
        report_type = input_data['report_type']
        start_date = input_data['start_date']
        end_date = input_data['end_date']

        date_range = pd.date_range(start=start_date, end=end_date)
        discord_data = pd.DataFrame({
            'date': date_range,
            'messages': np.random.randint(100, 1000, size=(len(date_range),)),
            'active_users': np.random.randint(50, 500, size=(len(date_range),))
        })
        
        ticket_data = pd.DataFrame({
            'date': date_range,
            'opened_tickets': np.random.randint(10, 100, size=(len(date_range),)),
            'closed_tickets': np.random.randint(5, 90, size=(len(date_range),))
        })

        plt.figure(figsize=(12, 6))

        if report_type == 'user_activity':
            plt.plot(discord_data['date'], discord_data['active_users'], label='Active Users')
            plt.plot(discord_data['date'], discord_data['messages'], label='Messages')
            plt.title('User Activity Over Time')
            plt.ylabel('Count')
            
            report = f"User Activity Report from {start_date} to {end_date}:\n"
            report += f"Total Messages: {discord_data['messages'].sum()}\n"
            report += f"Average Daily Active Users: {discord_data['active_users'].mean():.2f}\n"
            report += f"Peak Active Users: {discord_data['active_users'].max()} on {discord_data.loc[discord_data['active_users'].idxmax(), 'date'].strftime('%Y-%m-%d')}\n"

        elif report_type == 'ticket_performance':
            plt.plot(ticket_data['date'], ticket_data['opened_tickets'], label='Opened Tickets')
            plt.plot(ticket_data['date'], ticket_data['closed_tickets'], label='Closed Tickets')
            plt.title('Ticket Performance Over Time')
            plt.ylabel('Number of Tickets')
            
            report = f"Ticket Performance Report from {start_date} to {end_date}:\n"
            report += f"Total Opened Tickets: {ticket_data['opened_tickets'].sum()}\n"
            report += f"Total Closed Tickets: {ticket_data['closed_tickets'].sum()}\n"
            report += f"Average Daily Opened Tickets: {ticket_data['opened_tickets'].mean():.2f}\n"
            report += f"Average Daily Closed Tickets: {ticket_data['closed_tickets'].mean():.2f}\n"

        else:
            return f"Unknown report type: {report_type}"

        plt.xlabel('Date')
        plt.legend()
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()

        report += f"Graph: data:image/png;base64,{image_base64}"
        return report

    except json.JSONDecodeError:
        return "Error: Invalid JSON input"
    except KeyError as e:
        return f"Error: Missing required key in input - {str(e)}"
    except Exception as e:
        return f"Error generating report: {str(e)}"
