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
    embed = nextcord.Embed(
        title="YUUKI BOT COMMAND LIST",
        description="**USE `y!chat <message>` TO CHAT WITH YUUKI**",
        color=0x00ff00
    )

    embed.add_field(
        name="1. URL SHORTENER",
        value="`y!short <link>` - Shorten your URL.",
        inline=False
    )

    embed.add_field(
        name="2. MUSIC PLAYER",
        value=(
            "`y!play <title>` - Play music.\n"
            "`y!play <youtube link>` - Play music.\n"
            "`y!pause` - Pause the music.\n"
            "`y!resume` - Resume the music.\n"
            "`y!skip` - Skip the current music.\n"
            "`y!q` - View the queue.\n"
            "`y!remove <song index>` - Remove a song from the queue.\n"
            "`y!stop` - Disconnect the bot from the voice channel."
        ),
        inline=False
    )

    embed.add_field(
        name="3. WEATHER FORECAST",
        value=(
            "`y!setw <#channel> <city> <time>` - Set a weather forecast.\n"
            "`y!stopw` - Stop the weather forecast.\n"
            "`y!startw` - Restart the weather forecast.\n"
            "`y!checkw <city>` - Get the current weather."
        ),
        inline=False
    )

    embed.add_field(
        name="4. EPIC GAMES",
        value=(
            "`y!cg` - Check free games in Epic Games Store.\n"
            "`y!seteg <#channel>` - Set reminders for free games.\n"
            "`y!stopeg` - Stop free game notifications.\n"
            "`y!scheg <HH:MM>` - Schedule daily free game reminders.\n"
            "`y!setegr <role mention>` - Set a role to tag on free game reminders.\n"
            "`y!rmvegr <role mention>` - Remove a role from free game reminders.\n"
            "`y!checkegr` - Check what role will be tagged.\n"
            "`y!ce` - View all Epic Games settings."
        ),
        inline=False
    )

    embed.add_field(
        name="5. TASK REMINDER",
        value=(
            "`y!at <\"taskname\"> <\"YYYY-MM-DD HH:MM\">` - Add a task.\n"
            "`y!rmvt <\"taskname\">` - Remove a task.\n"
            "`y!lt` - View all tasks and their deadlines.\n"
            "`y!setre <\"taskname\"> <hours>` - Set a reminder before a task's deadline.\n"
            "`y!setrec <#channel>` - Set the channel for task notifications.\n"
            "`y!compt <\"taskname\">` - Mark a task as completed.\n"
            "`y!ct` - Delete all tasks."
        ),
        inline=False
    )

    embed.add_field(
        name="6. STEAM",
        value=(
            "`y!ss <game name>` - Search for a game on Steam.\n"
            "`y!setst <#channel>` - Set a reminder for Steam discounted games.\n"
            "`y!setstp <price>` - Set a maximum price for Steam reminders.\n"
            "`y!stopst` - Stop Steam reminders.\n"
            "`y!schst <HH:MM>` - Schedule daily Steam discounted game notifications."
        ),
        inline=False
    )

    embed.set_footer(text="Yuuki Bot | Developed by Nact with ❤️")

    await ctx.send(embed=embed)

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
