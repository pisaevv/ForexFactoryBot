import requests
import json
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
import discord
from discord.ext import commands, tasks
import asyncio
from flask import Flask
from threading import Thread
import pytz
from dateutil import parser as date_parser

CACHE_FILE = Path(__file__).parent / "cached_events.json"

# Initialize the Discord Bot with intents
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Get bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 5000))

# Define the timezone you want to use
TIMEZONE = 'America/New_York'  # Change this to your desired timezone


@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}!")
    # Start the scheduled daily fetch task
    daily_scheduled_fetch.start()


# Function to fetch ForexFactory events from the JSON endpoint or cache
async def fetch_forex_factory_events():
    """Fetch ForexFactory events from cache or API"""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cached_data = f.read()
            return json.loads(cached_data)
    
    try:
        response = requests.get(
            "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
            timeout=10
        )
        
        if response.status_code == 429:
            print("Rate limit exceeded. Please try again later.")
            raise Exception("Rate limit exceeded")
        
        if response.status_code != 200:
            print(f"Failed to fetch data, status code: {response.status_code}")
            raise Exception("Failed to fetch data")
        
        data = response.json()
        
        events = []
        for event in data:
            events.append({
                'title': event.get('title'),
                'country': event.get('country'),
                'date': event.get('date'),
                'time': event.get('time'),
                'impact': event.get('impact'),
                'forecast': event.get('forecast'),
                'previous': event.get('previous')
            })
        
        # Cache the data locally
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2)
        
        return events
    
    except requests.exceptions.RequestException as error:
        print(f"Error fetching ForexFactory events: {error}")
        raise


# Schedule a job to run every day at 6:10 AM in the specified timezone
@tasks.loop(hours=24)
async def daily_scheduled_fetch():
    """Daily scheduled task to fetch and send events"""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    
    # Calculate next run time at 6:10 AM
    next_run = now.replace(hour=6, minute=10, second=0, microsecond=0)
    if now >= next_run:
        next_run += timedelta(days=1)
    
    # Wait until 6:10 AM
    wait_seconds = (next_run - now).total_seconds()
    await asyncio.sleep(wait_seconds)
    
    print("Running daily scheduled fetch...")
    
    try:
        events = await fetch_forex_factory_events()
        if len(events) > 0:
            print("Fetched and cached daily events.")
            await send_weekly_events_to_all_channels(events)
        else:
            print("No events found.")
    except Exception as error:
        print(f"Error during scheduled fetch: {error}")


# Function to handle the command and output events for the entire week
async def send_weekly_events(channel, events):
    """Send weekly events to a channel"""
    try:
        today = datetime.now()
        # Start of the week (Sunday)
        start_of_week = today - timedelta(days=today.weekday() + 1)
        start_of_week = start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        # End of the week (Saturday)
        end_of_week = start_of_week + timedelta(days=6)
        end_of_week = end_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # Filter events for the current week with specific impact and currency conditions
        weekly_events = []
        for event in events:
            try:
                event_date = date_parser.parse(event['date'])
                is_within_week = start_of_week <= event_date <= end_of_week
                is_high_impact = event['impact'] == "High"
                is_medium_impact_eur_or_usd = (
                    event['impact'] == "Medium" and 
                    (event['country'] == "EUR" or event['country'] == "USD")
                )
                
                if is_within_week and (is_high_impact or is_medium_impact_eur_or_usd):
                    weekly_events.append(event)
            except Exception:
                continue
        
        if len(weekly_events) > 0:
            message = "This Week's Medium and High impact events:\n"
            messages = []
            
            for event in weekly_events:
                # Convert event date to a Date object
                event_date = date_parser.parse(event['date'])
                
                # Adjust the time to UTC+3
                utc3_date = event_date + timedelta(hours=3)
                
                # Format the date and time in UTC+3
                event_date_string = utc3_date.strftime('%A, %B %d, %Y')
                event_time = utc3_date.strftime('%H:%M')
                
                # Determine the impact flag
                impact_flag = "🔴" if event['impact'] == "High" else "🟡"
                
                event_message = (
                    f"- **{event['title']}** on **{event_date_string}** at "
                    f"**{event_time}** ({event['country']}):\n"
                    f"  Impact: {impact_flag} {event['impact']}\n\n"
                )
                
                # Check if adding the new event message would exceed Discord's message character limit
                if len(message + event_message) > 2000:
                    messages.append(message)
                    message = event_message
                else:
                    message += event_message
            
            messages.append(message)
            
            for msg in messages:
                await channel.send(msg)
        else:
            await channel.send("No Medium or High impact events found for this week.")
    
    except Exception as error:
        print(f"Error fetching weekly events: {error}")
        await channel.send("An error occurred while fetching the events.")


# Function to handle the command and output events for the current day
async def send_daily_events(channel):
    """Send daily events to a channel"""
    try:
        events = await fetch_forex_factory_events()
        current_date = datetime.now().strftime('%Y-%m-%d')  # Get current date in YYYY-MM-DD format
        
        # Filter events for the current day with specific impact and currency conditions
        daily_events = []
        for event in events:
            is_high_impact = event['impact'] == "High"
            is_medium_impact_eur_or_usd = (
                event['impact'] == "Medium" and 
                (event['country'] == "EUR" or event['country'] == "USD")
            )
            
            if event['date'].startswith(current_date) and (is_high_impact or is_medium_impact_eur_or_usd):
                daily_events.append(event)
        
        if len(daily_events) > 0:
            message = "Today's Medium and High impact events:\n"
            messages = []
            
            for event in daily_events:
                # Convert event date to a Date object
                event_date = date_parser.parse(event['date'])
                
                # Adjust the time to UTC+3
                utc3_date = event_date + timedelta(hours=3)
                
                # Format the time in UTC+3
                event_time = utc3_date.strftime('%H:%M')
                
                # Determine the impact flag
                impact_flag = "🔴" if event['impact'] == "High" else "🟡"
                
                event_message = (
                    f"- **{event['title']}** at **{event_time}** ({event['country']}):\n"
                    f"  Impact: {impact_flag} {event['impact']}\n\n"
                )
                
                # Check if adding the new event message would exceed Discord's message character limit
                if len(message + event_message) > 2000:
                    messages.append(message)
                    message = event_message
                else:
                    message += event_message
            
            messages.append(message)
            
            for msg in messages:
                await channel.send(msg)
        else:
            await channel.send("No Medium or High impact events found for today.")
    
    except Exception as error:
        print(f"Error fetching daily events: {error}")
        await channel.send("An error occurred while fetching the events.")


# Handle message commands
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.content == "!weeklyevents":
        events = await fetch_forex_factory_events()
        await send_weekly_events(message.channel, events)
    elif message.content == "!dailyevents":
        await send_daily_events(message.channel)
    
    # Process other commands
    await bot.process_commands(message)


async def send_weekly_events_to_all_channels(events):
    """Send weekly events to all channels where bot has permissions"""
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                # Check if bot has permission to send messages
                permissions = channel.permissions_for(guild.me)
                if permissions.send_messages:
                    await send_weekly_events(channel, events)
            except Exception as error:
                print(f"Error sending events to channel: {channel.id}", error)


# Express server equivalent using Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Express on Vercel"


def run_flask():
    """Run Flask server in a separate thread"""
    app.run(host='0.0.0.0', port=PORT)


# Main execution
if __name__ == "__main__":
    # Start Flask server in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Run the Discord bot
    bot.run(BOT_TOKEN)
