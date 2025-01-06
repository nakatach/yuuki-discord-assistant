import nextcord
from nextcord.ext import commands, tasks
import requests
from datetime import datetime, time
import os
from dotenv import load_dotenv

load_dotenv()

class SteamNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.steam_channel_id = None
        self.steam_price_limit = None
        self.scheduled_time = None
        self.start_notifier.start()

    def is_admin_or_owner(self, ctx):
        """Check if the user is an admin or the bot owner."""
        user_id = os.getenv("USER_ID")
        return ctx.author.guild_permissions.administrator or str(ctx.author.id) == user_id

    @commands.command(name="ss")
    async def search_steam(self, ctx, *args):
        """Search for a game on Steam by name and optional price."""
        if len(args) == 1 and args[0].isdigit():
            max_price = int(args[0])
            games = self.search_steam_games(max_price=max_price)
        else:
            game_name = " ".join(args)
            games = self.search_steam_games(game_name=game_name)
        
        if games:
            message = "**Search Results on Steam:**\n"
            for game in games[:10]:
                message += (
                    f"🎮 **{game['name']}**\n"
                    f"💸 Price: {game['price']}\n"
                    f"🔗 [Link to Steam Store]({game['url']})\n\n"
                )
            await ctx.send(message)
        else:
            await ctx.send("❌ No results found for that search.")

    @commands.command(name="setstp")
    async def set_steam_price(self, ctx, price: int):
        """Set the maximum price (in Rupiah) for game discount notifications."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ You do not have permission to use this command.")
            return

        if price < 0:
            await ctx.send("❌ Invalid price.")
            return

        self.steam_price_limit = price
        await ctx.send(f"✅ Maximum price for discount notifications set to Rp {price:,}.")

    @commands.command(name="setst")
    async def set_steam_channel(self, ctx, channel: nextcord.TextChannel):
        """Set the channel for Steam discount notifications."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ You do not have permission to use this command.")
            return

        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ I do not have permission to send messages to {channel.mention}.")
            return

        self.steam_channel_id = channel.id
        await ctx.send(f"✅ Steam Notifications channel set to {channel.mention}.")

    @commands.command(name="schst")
    async def schedule_steam(self, ctx, time_str: str):
        """Schedule the time for daily Steam discount notifications."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ You do not have permission to use this command.")
            return

        try:
            target_time = datetime.strptime(time_str, "%H:%M").time()
            self.scheduled_time = target_time
            await ctx.send(f"✅ Steam discount notifications will be sent every day at {time_str}.")
        except ValueError:
            await ctx.send("❌ Invalid time format. Use HH:MM format.")

    @commands.command(name="stopst")
    async def stop_steam(self, ctx):
        """Stop daily Steam discount notifications."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ You do not have permission to use this command.")
            return

        self.scheduled_time = None
        await ctx.send("✅ Daily Steam discount notifications have been stopped.")

    @tasks.loop(minutes=1)
    async def start_notifier(self):
        """Task loop for automatic notifications."""
        if self.scheduled_time and datetime.now().time().hour == self.scheduled_time.hour and datetime.now().time().minute == self.scheduled_time.minute:
            if self.steam_channel_id and self.steam_price_limit:
                channel = self.bot.get_channel(self.steam_channel_id)
                if channel:
                    games = self.get_discounted_games()
                    if games:
                        message = "**Discounted Games on Steam Below Maximum Price:**\n"
                        for game in games:
                            message += (
                                f"🎮 **{game['name']}**\n"
                                f"💸 Discounted Price: Rp {game['price']:,}\n"
                                f"🔗 [Link to Steam Store]({game['url']})\n\n"
                            )
                        await channel.send(message)

    def search_steam_games(self, game_name=None, max_price=None):
        """Search for games on Steam by name and price (optional)."""
        url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&cc=ID&l=indonesian"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Error: Steam API returned status {response.status_code}")
                return []

            data = response.json()
            games = []

            for game in data.get("items", []):
                price_data = game.get("price", {})
                if isinstance(price_data, dict):
                    initial_price = price_data.get("initial", 0) / 100
                    final_price = price_data.get("final", 0) / 100
                    price = f"Rp {int(final_price):,}" if final_price else "Free"
                else:
                    price = "Free" if price_data == 0 else f"Rp {int(price_data) / 100:,}"

                if max_price and final_price and final_price <= max_price:
                    games.append({
                        "name": game["name"],
                        "price": price,
                        "url": f"https://store.steampowered.com/app/{game['id']}"
                    })
                elif not max_price:
                    games.append({
                        "name": game["name"],
                        "price": price,
                        "url": f"https://store.steampowered.com/app/{game['id']}"
                    })

            return games
        except Exception as e:
            print(f"Error when fetching data from Steam API: {e}")
            return []

    def get_discounted_games(self):
        """Get a list of games with discounts below the maximum price."""
        url = "https://store.steampowered.com/api/featuredcategories/?cc=ID&l=indonesian"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Error: Steam API returned status {response.status_code}")
                return []

            data = response.json()
            games = []

            for game in data.get("specials", {}).get("items", []):
                original_price = game.get("original_price", 0) / 100
                discounted_price = game.get("final_price", 0) / 100

                if discounted_price <= self.steam_price_limit:
                    games.append({
                        "name": game["name"],
                        "price": discounted_price,
                        "url": f"https://store.steampowered.com/app/{game['id']}"
                    })

            return games
        except Exception as e:
            print(f"Error when fetching data from Steam API: {e}")
            return []

def setup(bot):
    bot.add_cog(SteamNotifier(bot))