import nextcord
from nextcord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='y!', intents=intents)

@bot.command(name="h")
async def send_help_message(ctx):
    await ctx.send("""
**YUUKI BOT COMMAND LIST**
**USE `y!chat <message>` TO CHAT WITH YUUKI**

1. **URL SHORTENER**
   Use `y!shorten <link>` to shorten your URL.

2. **MUSIC PLAYER**
   Use `y!play <title>` to play music.
   Use `y!play <youtube link>` to play music.
   Use `y!pause` to pause.
   Use `y!resume` to resume.
   Use `y!skip` to skip the current music.
   Use `y!q` to see the queue.
   Use `y!remove <song index>` to remove a song from the queue.
   Use `y!stop` to disconnect the bot from the voice channel.

3. **WEATHER FORECAST**
   Use `y!setweather <#channel> <city> <time>` to set a weather forecast.
   Use `y!stopweather` to stop the weather forecast.
   Use `y!startweather` to restart the weather forecast.
   Use `y!checkweather <city>` to get the current weather.

4. **EPIC GAMES**
   Use `y!checkgames` to check free games in Epic Games Store.
   Use `y!setepicgames <#channel>` to set reminders for free games.
   Use `y!stopepicgames` to stop free game notifications.
   Use `y!scheduleepic <HH:MM>` to schedule daily free game reminders.
                   
5. **TASK REMINDER**
   Use `y!addtask <"taskname"> <"YYYY-MM-DD HH:MM">` to add a task.
   Use `y!removetask <"taskname">` to remove a task.
   Use `y!listtasks` to view all the task and their deadline.
   Use `y!setreminder <"taskname"> <hours>` to set a reminder before a task's deadline.
   Use `y!setreminderchannel <#channel>` to set the channel for task notification.
   Use `y!completetask <"taskname">` to mark a task as completed.
   Use `y!cleartask` to view all tasks.
                   
6. **STEAM**
   Use `y!searchsteam <game name>` to search game on Steam.
   Use `y!setsteam <#channel>` to set a reminder for Steam discounted games.
   Use `y!setsteamprice <prices without commas or dots>` to set a maximum price for Steam reminder.
   Use `y!stopsteam` to stop Steam reminder.
   Use `y!schedulesteam <HH:MM>` to schedule daily Steam discounted games notification.
    """)

extensions = [
    "url_shortener",
    "weather",
    "music_player",
    "epicgames",
    "taskreminder",
    "chatbot",
    "steam",
]

for ext in extensions:
    try:
        bot.load_extension(ext)
    except Exception as e:
        print(f"Failed to load extension {ext}: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as: {bot.user.name}")

if __name__ == '__main__':
    bot.run(TOKEN)