import nextcord
from nextcord.ext import commands, tasks
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from datetime import datetime
from dotenv import load_dotenv
import os
import pytz
import json

load_dotenv()

class EpicGamesNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.epic_channels = self.load_data('epic_channels.json')
        self.role_to_tag = self.load_data('role_to_tag.json')
        self.scheduled_time = None
        self.previous_games = []
        self.start_notifier.start()

    def load_data(self, filename):
        """Load data from a JSON file if it exists; if not, create a new file."""
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return json.load(f)
        return {}

    def save_data(self, filename, data):
        """Save data to a JSON file."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)

    def is_admin_or_owner(self, ctx):
        """Check if the user is an admin or the bot owner"""
        user_id = os.getenv("USER_ID")
        return ctx.author.guild_permissions.administrator or str(ctx.author.id) == user_id

    @commands.command(name="searcheg")
    async def search_epic(self, ctx, *, game_name):
        """Search for a game on the Epic Games Store by name"""
        games = self.search_epic_games(game_name)
        if games:
            message = "**Search Results on the Epic Games Store:**\n"
            for game in games[:5]:
                message += (
                    f"🎮 **{game['title']}**\n"
                    f"{game['description']}\n"
                    f"💸 Price: {game['price']}\n"
                    f"🔗 [Link to Epic Games Store]({game['url']})\n\n"
                )
            await ctx.send(message)
        else:
            await ctx.send("❌ No result found for the search.")

    def search_epic_games(self, game_name):
        """Searching for a game on the Epic Games Store by name"""
        url = "https://store.epicgames.com/api/content/v2/catalog"
        params = {
            "keywords": game_name,
            "category": "games",
            "locale": "en-US",
            "count": 10,
        }
        try:
            response = self.get_with_retry(url, params=params)
            if response.status_code != 200:
                print(f"Error: API return status {response.status_code}")
                return []

            data = response.json()
            games = []

            for element in data.get("elements", []):
                title = element.get("title", "Unknown")
                description = element.get("description", "No description.")
                price_info = element.get("price", {}).get("totalPrice", {}).get("fmtPrice", {})
                price = price_info.get("originalPrice", "Unknown")
                games.append({
                    "title": title,
                    "description": description,
                    "price": price,
                    "url": f"https://store.epicgames.com/p/{title.replace(' ', '-').lower()}",
                })

            return games
        except Exception as e:
            print(f"Error while fetching data from the API: {e}")
            return []

    def get_with_retry(self, url, params=None):
        """A function to make requests with retry"""
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session.get(url, params=params, timeout=30)

    @commands.command(name="cg")
    async def check_games(self, ctx):
        """Check the free games currently available on the Epic Games Store."""
        games = self.get_free_games()
        if games:
            message = "**Free Games on Epic Games Right Now:**\n"
            for game in games:
                message += (
                    f"🎮 **{game['title']}**\n"
                    f"{game['description']}\n"
                    f"📅 Free from {game['start_date']} to {game['end_date']}\n"
                    f"🔗 [Claim Now](https://store.epicgames.com/p/{game['title'].replace(' ', '-').lower()})\n\n"
                )
            await ctx.send(message)
        else:
            await ctx.send("⚠️ No free games available right now.")

    @commands.command(name="seteg")
    async def set_epic_games_channel(self, ctx, channel: nextcord.TextChannel):
        """Set the channel for Epic Games free game notifications in this server."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ You do not have permission to use this command.")
            return

        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ I do not have permission to send messages to {channel.mention}.")
            return

        self.epic_channels[ctx.guild.id] = channel.id
        self.save_data('epic_channels.json', self.epic_channels)
        await ctx.send(f"✅ Epic Games Notifications channel for this server has been set to {channel.mention}")

    @commands.command(name="scheg")
    async def schedule_epic(self, ctx, time: str):
        """Schedule the Epic Games game notification message."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ You do not have permission to use this command.")
            return

        try:
            timezone = pytz.timezone('Asia/Jakarta')
            target_time = datetime.strptime(time, "%H:%M").time()

            now = datetime.now(timezone)
            target_datetime = datetime.combine(now.date(), target_time)
            self.scheduled_time = target_time
            await ctx.send(f"✅ The notification will be sent every day at {time}.")
        except ValueError:
            await ctx.send("❌ Invalid time format. Use HH:MM format.")

    @commands.command(name="stopeg")
    async def stop_epic_notifications(self, ctx):
        """Stop the Epic Games free game notification feature."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ You do not have permission to use this command.")
            return

        self.scheduled_time = None
        await ctx.send("✅ Epic Games free game notifications have been stopped.")

    @commands.command(name="setegr")
    async def set_role(self, ctx, role: nextcord.Role):
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ You do not have permission to use this command.")
            return
        
        self.role_to_tag[ctx.guild.id] = role.id
        self.save_data('role_to_tag.json', self.role_to_tag)
        await ctx.send(f"✅ The role {role.mention} has been set to be tagged in the free game notifications.")

    @commands.command(name="rmvegr")
    async def remove_epic_games_role(self, ctx, role: nextcord.Role):
        """Remove the role assigned to free game notifications in Epic Games."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ You do not have permission to use this command.")
            return

        if ctx.guild.id in self.role_to_tag and self.role_to_tag[ctx.guild.id] == role.id:
            del self.role_to_tag[ctx.guild.id]
            self.save_data('role_to_tag.json', self.role_to_tag)
            await ctx.send(f"✅ The role {role.mention} has been removed from the free game notifications.")
        else:
            await ctx.send(f"⚠️ The role {role.mention} is not found in the settings for notifications in this server.")

    @commands.command(name="checkegr")
    async def check_epic_games_role(self, ctx):
        """Display the role that will be tagged in the free game notifications."""
        role_id = self.role_to_tag.get(ctx.guild.id)
        if role_id:
            role = ctx.guild.get_role(role_id)
            await ctx.send(f"✅ The role that will be tagged in this server is: {role.mention}")
        else:
            await ctx.send("⚠️ No role has been set for notifications in this server.")

    @commands.command(name="ce")
    async def check_epic(self, ctx):
        """View the free game notification settings for this server."""
        guild_id = ctx.guild.id

        if guild_id in self.epic_channels:
            channel = self.bot.get_channel(self.epic_channels[guild_id])
            channel_info = f"Notification channel: {channel.mention}" if channel else "Channel not found."
        else:
            channel_info = "Notification channel has not been set."

        if guild_id in self.role_to_tag:
            role = ctx.guild.get_role(self.role_to_tag[guild_id])
            role_info = f"Role that is tagged: {role.mention}" if role else "Role to be tagged not found."
        else:
            role_info = "Role to be tagged has not been set."

        if self.scheduled_time:
            schedule_info = f"Notifications are scheduled every day at {self.scheduled_time.strftime('%H:%M')}."
        else:
            schedule_info = "No schedule set for notifications."

        message = (
            "**Epic Games Free Game Notification Settings in This Server:**\n"
            f"{channel_info}\n"
            f"{role_info}\n"
            f"{schedule_info}\n"
        )

        await ctx.send(message)

    @tasks.loop(minutes=1)
    async def start_notifier(self):
        """Task loop for automatic notifications in all servers."""
        games = self.get_free_games()
        if not games:
            return

        new_games = [game for game in games if game not in self.previous_games]

        if new_games:
            for guild_id, channel_id in self.epic_channels.items():
                channel = self.bot.get_channel(channel_id)
                if channel:
                    role_id = self.role_to_tag.get(guild_id)
                    role_mention = f"<@&{role_id}>" if role_id else "everyone"
                    message = f"**New Free Games on Epic Games Right Now:**\n{role_mention}\n"
                    for game in new_games:
                        message += (
                            f"🎮 **{game['title']}**\n"
                            f"{game['description']}\n"
                            f"📅 Free from {game['start_date']} to {game['end_date']}\n"
                            f"🔗 [Claim Now](https://store.epicgames.com/p/{game['title'].replace(' ', '-').lower()})\n\n"
                        )
                    await channel.send(message)

            self.previous_games = games

    def get_free_games(self):
        """Get free games data from the Epic Games Store API."""
        url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        try:
            response = self.get_with_retry(url)
            if response.status_code != 200:
                print(f"Error: API returned status {response.status_code}")
                return []

            data = response.json()
            games = []

            for game in data["data"]["Catalog"]["searchStore"]["elements"]:
                if game.get("promotions") and game["promotions"].get("promotionalOffers"):
                    offers = game["promotions"]["promotionalOffers"][0]["promotionalOffers"]
                    for offer in offers:
                        start_date = offer["startDate"]
                        end_date = offer["endDate"]
                        price_info = game.get("price", {}).get("totalPrice", {})
                        if price_info.get("originalPrice", 0) == 0:
                            games.append({
                                "title": game["title"],
                                "description": game.get("description", "No description."),
                                "start_date": datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d %B %Y"),
                                "end_date": datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d %B %Y"),
                            })
            return games
        except Exception as e:
            print(f"Error while fetching data from API: {e}")
            return []

def setup(bot):
    bot.add_cog(EpicGamesNotifier(bot))
