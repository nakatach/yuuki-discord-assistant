# Yuuki Discord Bot

A Discord bot built with Groq, designed to assist with daily tasks and provide companionship through its chatbot feature.

## Features

- Chat with Yuuki, powered by Groq's Llama-3.3-70b versatile model.
- Chat responses with two distinct personalities—cold and romantic—that can be customized based on the user's Discord ID.
- Weather information integration and reminder
- Epic Games's free games reminder and checker
- Task reminder
- Regular commands
- To-do list
- URL shortener using Cuttly API
- Music player using Youtube and Youtube cookies

## Commands

- **URL SHORTENER**
   Use `y!shorten <link>` to shorten your URL.

- **MUSIC PLAYER**
  - Use `y!play <title>` to play music.
  - Use `y!play <youtube link>` to play music.
  - Use `y!pause` to pause.
  - Use `y!resume` to resume.
  - Use `y!skip` to skip the current music.
  - Use `y!q` to see the queue.
  - Use `y!remove <song index>` to remove a song from the queue.
  - Use `y!stop` to disconnect the bot from the voice channel.

- **WEATHER FORECAST**
  - Use `y!setweather <#channel> <city> <time>` to set a weather forecast.
  - Use `y!stopweather` to stop the weather forecast.
  - Use `y!startweather` to restart the weather forecast.
  - Use `y!checkweather <city>` to get the current weather.

- **EPIC GAMES**
  - Use `y!checkgames` to check free games in Epic Games Store.
  - Use `y!setepicgames <#channel>` to set reminders for free games.
  - Use `y!stopepicgames` to stop free game notifications.
  - Use `y!setepicdm <@user>` to receive free game reminders via DM.
  - Use `y!setepicinterval <hours>` to set the notification interval.
  - Use `y!scheduleepic <HH:MM>` to schedule daily free game reminders.
  - Use `y!epicstats` to view statistics for Epic Games notifications.
                   
- **TASK REMINDER**
  - Use `y!addtask <"taskname"> <"YYYY-MM-DD HH:MM">` to add a task.
  - Use `y!removetask <"taskname">` to remove a task.
  - Use `y!listtasks` to view all the task and their deadline.
  - Use `y!setreminder <"taskname"> <hours>` to set a reminder before a task's deadline.
  - Use `y!setreminderchannel <#channel>` to set the channel for task notification.
  - Use `y!completetask <"taskname">` to mark a task as completed.
  - Use `y!cleartask` to view all tasks.

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/your-bot-repo.git
cd your-bot-repo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your tokens:
```
DISCORD_BOT_TOKEN=your_discord_bot_token_here
CUTTLY_API_KEY=your_cuttly_api_key_here
GROQ_API_KEY=your_groq_api_key_here
USER_ID=your_discord_user_id_here
```

4. Run the bot:
```bash
python main.py
```

## Deployment

### Local Development
1. Set up your virtual environment
2. Install dependencies
3. Create `.env` file
4. Run the bot

### Hosting Platforms
- **PylexNodes**
- **Heroku**
- **pella**

## Environment Variables

Create a `.env` file with the following:
- DISCORD_BOT_TOKEN=your_discord_bot_token_here
- CUTTLY_API_KEY=your_cuttly_api_key_here
- GROQ_API_KEY=your_groq_api_key_here
- USER_ID=your_discord_user_id_here
- 
## Contributing

Feel free to submit issues and pull requests!
