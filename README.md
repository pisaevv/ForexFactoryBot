# 📊 Forex Factory Event Bot

Stay informed about the most impactful Forex events — right from your 
Discord server.

---

## 📝 Introduction

This bot fetches upcoming ForexFactory economic events and delivers them 
directly into your Discord channels. Designed to focus on **Medium** and 
**High-impact** events for **USD** and **EUR**, this bot ensures traders 
and forex enthusiasts stay one step ahead of the market without ever 
leaving Discord.

Whether you're running a trading community or keeping tabs on economic 
news, this bot automates event notifications and schedules daily or weekly 
digests.

---

## 💡 Features

- 📅 Fetches **daily and weekly Forex economic events**.
- 🔔 Filters for **High-impact** and **Medium-impact EUR/USD** events.
- 🧠 Automatically caches API data for efficient lookups.
- 🌍 Adjusts timezones to suit your trading region.
- 🤖 Simple `!dailyevents` and `!weeklyevents` commands.
- ⚡ Scheduled daily event digests at 6:10 AM (configurable).

---

## 🗺️ How It Works
```
┌───────────────────────────────────────────────────────────────┐
│  ForexFactory JSON API                                       │
│     ↓ Fetch + Cache                                          │
│  Node.js Bot filters for relevant events                     │
│     ↓ Scheduled/On-Demand Delivery                           │
│  Discord Channels                                            │
└───────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Installation & Usage (For End-Users)

1. Clone the repository:
```bash
git clone https://github.com/pisaevv/ForexFactoryBot.git
cd ForexFactoryBot
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file:
```bash
BOT_TOKEN=your_discord_bot_token
PORT=5000
```

4. Start the bot:
```bash
node index.js
```

5. Invite the bot to your server with appropriate permissions (`Send 
Messages` in text channels).

---

## 💻 Development & Contribution

If you're a developer looking to contribute:

1. Fork this repository.
2. Clone your fork locally.
3. Run the dev server:
```bash
npm install
node index.js
```

4. Suggested tools:
   - Node.js `v18` or higher.
   - `nodemon` for local testing.

All event-fetching logic is cached via `cached_events.json` to reduce 
unnecessary API calls. Modify the scheduling logic (using `node-schedule`) 
to suit your timezones or trading habits.

Any issues can be relayed to me at - pisaevbislan@gmail.com

## 📢 Commands

| Command            | Description                                        
|
|--------------------|----------------------------------------------------|
| `!dailyevents`     | Displays today's Medium and High impact events.    
|
| `!weeklyevents`    | Displays this week's Medium and High impact 
events.|

---

## 📌 Notes

- Perfect for forex communities, market-watch groups, and trading servers.
- Add scheduled alerts or custom filtering logic as per your server's 
needs.

---

💡 PRs and ideas are welcome! Help make this bot smarter for the trading 
community.
