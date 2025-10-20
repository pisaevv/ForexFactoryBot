const request = require("request");
const fs = require("fs");
const path = require("path");
const {
  Client,
  GatewayIntentBits,
  PermissionsBitField,
} = require("discord.js");
const schedule = require("node-schedule");
const dateFormat = require("dateformat");
const moment = require("moment-timezone");

const CACHE_FILE = path.join(__dirname, "cached_events.json");

// Initialize the Discord Bot and set perms
const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent, 
  ],
});

client.login(process.env.BOT_TOKEN);

client.on("ready", () => {
  console.log(`Bot is online as ${client.user.tag}!`);
});

// Function to fetch ForexFactory events from the JSON endpoint or cache
async function fetchForexFactoryEvents() {
  if (fs.existsSync(CACHE_FILE)) {
    const cachedData = fs.readFileSync(CACHE_FILE, "utf-8");
    return JSON.parse(cachedData);
  }

  return new Promise((resolve, reject) => {
    request(
      "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
      { json: true },
      (error, response, data) => {
        if (error) {
          console.error("Error fetching ForexFactory events:", error);
          return reject(error);
        }

        if (response.statusCode === 429) {
          console.error("Rate limit exceeded. Please try again later.");
          return reject(new Error("Rate limit exceeded"));
        }

        if (response.statusCode !== 200) {
          console.error(
            "Failed to fetch data, status code:",
            response.statusCode,
          );
          return reject(new Error("Failed to fetch data"));
        }

        const events = data.map((event) => ({
          title: event.title,
          country: event.country,
          date: event.date,
          time: event.time,
          impact: event.impact,
          forecast: event.forecast,
          previous: event.previous,
        }));

        // Cache the data locally
        fs.writeFileSync(CACHE_FILE, JSON.stringify(events, null, 2));
        resolve(events);
      },
    );
  });
}

// Define the timezone you want to use
const timezone = 'America/New_York'; // Change this to your desired timezone

// Schedule a job to run every day at 6:10 AM in the specified timezone
schedule.scheduleJob('10 6 * * *', async () => {
  const now = moment().tz(timezone);
  console.log("Running daily scheduled fetch...");

  try {
    const events = await fetchForexFactoryEvents();
    if (events.length > 0) {
      console.log("Fetched and cached daily events.");
      await sendWeeklyEventsToAllChannels(events);
    } else {
      console.log("No events found.");
    }
  } catch (error) {
    console.error("Error during scheduled fetch:", error);
  }
});

// Function to handle the command and output events for the entire week
async function sendWeeklyEvents(channel, events) {
  try {
    const today = new Date();
    const startOfWeek = new Date(today.setDate(today.getDate() - today.getDay())); // Start of the week (Sunday)
    const endOfWeek = new Date(today.setDate(today.getDate() - today.getDay() + 6)); // End of the week (Saturday)

    // Filter events for the current week with specific impact and currency conditions
    const weeklyEvents = events.filter((event) => {
      const eventDate = new Date(event.date);
      const isWithinWeek = eventDate >= startOfWeek && eventDate <= endOfWeek;
      const isHighImpact = event.impact === "High";
      const isMediumImpactEURorUSD = event.impact === "Medium" && (event.country === "EUR" || event.country === "USD");
      return isWithinWeek && (isHighImpact || isMediumImpactEURorUSD);
    });

    if (weeklyEvents.length > 0) {
      let message = "This Week's Medium and High impact events:\n";
      let messages = [];

      weeklyEvents.forEach((event) => {
        // Convert event date to a Date object
        const eventDate = new Date(event.date);

        // Adjust the time to UTC+3
        const utc3Date = new Date(eventDate.getTime() + 3 * 60 * 60 * 1000);

        // Format the date and time in UTC+3
        const eventDateString = utc3Date.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
        const eventTime = utc3Date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });

        // Determine the impact flag
        const impactFlag = event.impact === "High" ? "🔴" : "🟠";

        const eventMessage = `- **${event.title}** on **${eventDateString}** at **${eventTime}** (${event.country}):\n  Impact: ${impactFlag} ${event.impact}\n\n`;

        // Check if adding the new event message would exceed Discord's message character limit
        if ((message + eventMessage).length > 2000) {
          messages.push(message);
          message = eventMessage;
        } else {
          message += eventMessage;
        }
      });

      messages.push(message);

      for (const msg of messages) {
        await channel.send(msg);
      }
    } else {
      channel.send("No Medium or High impact events found for this week.");
    }
  } catch (error) {
    console.error("Error fetching weekly events:", error);
    channel.send("An error occurred while fetching the events.");
  }
}

// Function to handle the command and output events for the current day
async function sendDailyEvents(channel) {
  try {
    const events = await fetchForexFactoryEvents();
    const currentDate = new Date().toISOString().split("T")[0]; // Get current date in YYYY-MM-DD format

    // Filter events for the current day with specific impact and currency conditions
    const dailyEvents = events.filter((event) => {
      const isHighImpact = event.impact === "High";
      const isMediumImpactEURorUSD = event.impact === "Medium" && (event.country === "EUR" || event.country === "USD");
      return event.date.startsWith(currentDate) && (isHighImpact || isMediumImpactEURorUSD);
    });

    if (dailyEvents.length > 0) {
      let message = "Today's Medium and High impact events:\n";
      let messages = [];

      dailyEvents.forEach((event) => {
        // Convert event date to a Date object
        const eventDate = new Date(event.date);

        // Adjust the time to UTC+3
        const utc3Date = new Date(eventDate.getTime() + 3 * 60 * 60 * 1000);

        // Format the time in UTC+3
        const eventTime = utc3Date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });

        // Determine the impact flag
        const impactFlag = event.impact === "High" ? "🔴" : "🟠";

        const eventMessage = `- **${event.title}** at **${eventTime}** (${event.country}):\n  Impact: ${impactFlag} ${event.impact}\n\n`;

        // Check if adding the new event message would exceed Discord's message character limit
        if ((message + eventMessage).length > 2000) {
          messages.push(message);
          message = eventMessage;
        } else {
          message += eventMessage;
        }
      });

      messages.push(message);

      for (const msg of messages) {
        await channel.send(msg);
      }
    } else {
      channel.send("No Medium or High impact events found for today.");
    }
  } catch (error) {
    console.error("Error fetching daily events:", error);
    channel.send("An error occurred while fetching the events.");
  }
}

// Handle message commands
client.on("messageCreate", async (message) => {
  if (message.author.bot) return;

  if (message.content === "!weeklyevents") {
    await sendWeeklyEvents(message.channel);
  } else if (message.content === "!dailyevents") {
    await sendDailyEvents(message.channel);
  }
});

const express = require("express");
const app = express(); 
app.get("/", (req, res) => { res.send("Express on Vercel"); }); 
const PORT = process.env.PORT || 5000; app.listen(PORT, () => {console.log(`Server is running on port ${PORT}`); });

async function sendWeeklyEventsToAllChannels(events) {
  const channels = client.channels.cache.filter(channel => 
    channel.type === 0 && // Text channels
    channel.permissionsFor(client.user).has(PermissionsBitField.Flags.SendMessages)
  );
  
  for (const channel of channels.values()) {
    try {
      await sendWeeklyEvents(channel, events);
    } catch (error) {
      console.error(`Error sending events to channel: ${channel.id}`, error);
    }
  }
}

async function sendWeeklyEvents(channel, events) {
  try {
    await sendWeeklyEvents(channel, events);
  } catch (error) {
    console.error(`Error sending events to channel: ${channel.id}`, error);
  }
}