import logging
import os
import smtplib
import aiohttp
from datetime import datetime
from typing import Annotated  # <--- Typo fixed here (was Annotateds)
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
import asyncio
from livekit.agents import function_tool, RunContext
from langchain_community.tools import DuckDuckGoSearchRun
import asyncio
from functools import partial
from livekit.agents.llm import function_tool
from livekit.agents import RunContext
from duckduckgo_search import DDGS

# 1. Load environment variables immediately
load_dotenv()

# --- WEATHER TOOL ---
@function_tool()
async def get_weather(
    context: RunContext, 
    city: str
) -> str:
    """
    Get the current weather for a given city asynchronously.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://wttr.in/{city}?format=3") as response:
                if response.status == 200:
                    text = await response.text()
                    logging.info(f"Weather for {city}: {text.strip()}")
                    return text.strip()
                else:
                    return f"Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather: {e}")
        return f"An error occurred while retrieving weather for {city}."

# --- WEB SEARCH TOOL ---
@function_tool()
async def search_web(
    context: RunContext, 
    query: str
) -> str:
    """
    Search the web using DuckDuckGo asynchronously.
    """
    try:
        # Use .arun() for the async version
        results = await DuckDuckGoSearchRun().arun(tool_input=query)
        logging.info(f"Search results for '{query}': {results}")
        return results
    except Exception as e:
        logging.error(f"Error searching web: {e}")
        return f"An error occurred while searching for '{query}'."

# --- JOKE TOOL ---
@function_tool()
async def fetch_joke(
    context: RunContext
) -> str:
    """
    Fetch a random joke from an external API asynchronously.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://official-joke-api.appspot.com/random_joke") as response:
                if response.status == 200:
                    joke_data = await response.json()
                    joke = f"{joke_data['setup']} - {joke_data['punchline']}"
                    return joke
                else:
                    return "Could not retrieve a joke at this time."
    except Exception as e:
        logging.error(f"Error fetching joke: {e}")
        return "An error occurred while fetching a joke."

# --- EMAIL TOOL ---
@function_tool()
async def send_email(
    to_email: Annotated[str, "The recipient's email address"],
    subject: Annotated[str, "The subject of the email"],
    message: Annotated[str, "The content/body of the email"],
    cc_email: Annotated[str, "Optional CC email address"] = ""
):
    """
    Sends an email using Gmail. Use this when the user asks to send an email.
    """
    print(f"DEBUG: Attempting email to {to_email}") 
    
    sender_email = os.getenv("GMAIL_SENDER")
    sender_password = os.getenv("GMAIL_APP_PASSWORD")

    if not sender_email or not sender_password:
        print("❌ ERROR: Credentials missing. Check .env file.")
        return "Error: Gmail credentials not configured."

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        if cc_email:
            msg['Cc'] = cc_email
            
        msg.attach(MIMEText(message, 'plain'))

        # Connect to Gmail via SMTP (Sync method wrapped in async function)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        
        print(f"✅ Email successfully sent to {to_email}")
        return f"Email sent to {to_email}!"

    except Exception as e:
        print(f"❌ SMTP Error: {str(e)}")
        return f"Failed to send email: {str(e)}"

# --- UTILITY TOOLS ---

@function_tool()
async def get_current_time(context: RunContext) -> str:
    """Get the current system time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@function_tool()
async def get_current_date(context: RunContext) -> str:
    """Get the current system date."""
    return datetime.now().strftime("%Y-%m-%d")

@function_tool()
async def echo_message(context: RunContext, message: str) -> str:
    """Echo back the provided message."""
    return message

@function_tool()
async def calculate_sum(context: RunContext, numbers: str) -> str:
    """Calculate the sum of a list of numbers provided as a comma-separated string."""
    try:
        num_list = [float(num.strip()) for num in numbers.split(',')]
        return f"The sum is {sum(num_list)}."
    except Exception as e:
        return f"Error calculating sum: {e}"

# --- STUB TOOLS (Placeholders) ---

@function_tool()
async def add_reminder(context: RunContext, reminder: str, time: str) -> str:
    return f"Reminder '{reminder}' set for {time}."

@function_tool()
async def list_reminders(context: RunContext) -> str:
    return "You have no reminders set."

@function_tool()
async def delete_reminder(context: RunContext, reminder_id: str) -> str:
    return f"Reminder with ID {reminder_id} deleted."

@function_tool()
async def notify_user(context: RunContext, notification: str) -> str:
    return f"User notified with message: {notification}"

@function_tool()
async def translate_text(context: RunContext, text: str, target_language: str) -> str:
    return f"Translated '{text}' to {target_language}."
@function_tool()
async def read_news(context: RunContext, topic: str) -> str:
    """
    Fetches the latest news headlines and summaries for a specific topic.
    Useful for getting real-time updates on current events, sports, or technology.
    """
    print(f"Fetching news for: {topic}")
    
    try:
        # DDGS is a blocking synchronous library, so we run it in a separate thread
        # to keep the agent's main loop responsive (preventing audio cutouts).
        loop = asyncio.get_running_loop()
        
        # We use partial to pass arguments to the synchronous function
        fetch_task = partial(DDGS().news, keywords=topic, max_results=5)
        results = await loop.run_in_executor(None, fetch_task)

        if not results:
            return f"I couldn't find any recent news stories regarding '{topic}'."

        # Format the output into a clear string the AI can read naturally
        formatted_news = [f"Here is the latest news on {topic}:"]
        
        for item in results:
            title = item.get('title', 'Untitled')
            source = item.get('source', 'Unknown Source')
            # 'body' usually contains the summary/snippet in DDGS
            summary = item.get('body', item.get('snippet', 'No details available.'))
            date = item.get('date', '')
            
            # Structure: "Title (Source) - Summary"
            formatted_news.append(f"- {title} ({source}, {date})\n  Summary: {summary}\n")

        return "\n".join(formatted_news)

    except Exception as e:
        # Log the error for debugging but return a clean message to the AI
        print(f"Error fetching news: {e}")
        return f"I encountered an error while searching for news on {topic}."

import webbrowser # Standard library
# ... keep your other imports ...

@function_tool()
async def play_video(
    context: RunContext, 
    topic: str
) -> str:
    """
    Plays a video on YouTube. Use this when the user asks to play a song or video.
    """
    print(f"📺 Request received: Play '{topic}' on YouTube")
    
    # 1. Try the advanced automation first
    try:
        import pywhatkit
        # We run this in a thread because it blocks execution
        await asyncio.to_thread(pywhatkit.playonyt, topic)
        return f"I've started playing {topic} on YouTube."
        
    except Exception as e:
        # 2. Fallback: Just open the search results in the default browser
        print(f"⚠️ pywhatkit failed ({e}), switching to standard browser open.")
        search_url = f"https://www.youtube.com/results?search_query={topic}"
        webbrowser.open(search_url)
        return f"I couldn't autoplay the specific video, but I've opened YouTube search results for {topic}."
    

@function_tool()
async def send_whatsapp(
    context: RunContext, 
    phone_number: str, 
    message: str
) -> str:
    """
    Sends a WhatsApp message to a specific phone number using browser automation.
    """
    import pywhatkit
    print(f"📱 Request received: WhatsApp to {phone_number}")
    
    # Cleanup phone number
    if not phone_number.startswith("+"):
        phone_number = "+91" + phone_number.strip() 
    
    try:
        # INCREASED WAIT TIME to 25 seconds
        # tab_close=False -> Keeps the window open so you can verify it sent
        await asyncio.to_thread(
            pywhatkit.sendwhatmsg_instantly, 
            phone_number, 
            message, 
            wait_time=25,   # <--- Increased from 15
            tab_close=False # <--- Changed to False so you can see the result
        )
        return f"I have opened WhatsApp and typed the message to {phone_number}. Please check if it sent."
        
    except Exception as e:
        print(f"❌ WhatsApp Error: {e}")
        return f"I tried to send the WhatsApp message, but it failed. Is WhatsApp Web logged in?"