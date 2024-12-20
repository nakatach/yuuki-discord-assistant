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
async def SendMessage(ctx):
    await ctx.send("""1. URL SHORTENER
Use <y!shorten> <link> to shorten your URL

2. MUSIC PLAYER
Use <y!play> <title> to play music
Use <y!pause> to pause
Use <y!resume> to resume
Use <y!skip> to skip the current music
Use <y!q> to see the queue
Use <y!remove> <song index> to remove a music from the queue
Use <y!stop> to disconnect the bot from the voice channel

3. TO DO LIST
Use <y!addtask> <taskname> to add a task to your to-do list
Use <y!removetask> <task index> to remove a task
Use <y!viewtasks> to see the to-do list
Use <y!clear> to remove all the tasks from the list
Use <y!completetask> <task index> to mark a task as completed

4. WEATHER FORECAST
Use <y!setweather> <#channel name> <time> to set a weather forecast
Use <y!stopweather> to stop the weather forecast
Use <y!startweather> to start the weather forecast that stopped before
Use <y!checkweather> <city name> to check the current weather

5. EPIC GAMES CHECKER
Use <y!checkgames> to check the current free games in Epic Games Store
Use <y!setepicgames> to set a reminder for free games in Epic Games Store
""")

@bot.command()
async def shorten(ctx, link: str):
    from url_shortener import shorten_link
    result = shorten_link(link)
    await ctx.send(result)

extensions = [
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