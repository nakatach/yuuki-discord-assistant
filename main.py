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

3. **TO-DO LIST**
   Use `y!addtask <taskname>` to add a task.
   Use `y!removetask <task index>` to remove a task.
   Use `y!viewtasks` to view the to-do list.
   Use `y!clear` to clear the to-do list.
   Use `y!completetask <task index>` to mark a task as completed.

4. **WEATHER FORECAST**
   Use `y!setweather <#channel> <city> <time>` to set a weather forecast.
   Use `y!stopweather` to stop the weather forecast.
   Use `y!startweather` to restart the weather forecast.
   Use `y!checkweather <city>` to get the current weather.

5. **EPIC GAMES CHECKER**
   Use `y!checkgames` to check free games in Epic Games Store.
   Use `y!setepicgames <#channel>` to set reminders for free games.
   Use `y!stopepicgames` to stop free game notifications.
   Use `y!setepicdm <@user>` to receive free game reminders via DM.
   Use `y!setepicinterval <hours>` to set the notification interval.
   Use `y!scheduleepic <HH:MM>` to schedule daily free game reminders.
   Use `y!epicstats` to view statistics for Epic Games notifications.

6. **CLASS REMINDER**
   Use `y!addclass <subject> <day> <time>` to add a class reminder.
   Use `y!removeclass <class index>` to remove a class.
   Use `y!viewclasses` to view all class reminders.
    """)

extensions = [
    "url_shortener",
    "weather",
    "class_reminder",
    "music_player",
    "to_do_list",
    "epicgames"
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