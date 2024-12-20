import nextcord
from nextcord.ext import commands, tasks
import requests
from datetime import datetime, timezone

class EpicGamesNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.epic_channel_id = None
        self.start_notifier.start()

    @commands.command(name="setepicgames")
    async def set_epic_games_channel(self, ctx, channel: nextcord.TextChannel):
        """Set channel untuk pemberitahuan game gratis Epic Games."""
        self.epic_channel_id = channel.id
        await ctx.send(f"✅ Channel Epic Games Notifications telah diatur ke {channel.mention}")

    @commands.command(name="stopepicgames")
    async def stop_epic_games(self, ctx):
        """Hentikan pemberitahuan game gratis Epic Games."""
        self.epic_channel_id = None
        await ctx.send("❌ Pemberitahuan Epic Games telah dihentikan.")

    @commands.command(name="checkgames")
    async def check_games(self, ctx):
        """Cek game yang sedang gratis di Epic Games Store."""
        games = self.get_free_games()
        if games:
            message = "**Game Gratis di Epic Games Saat Ini:**\n"
            for game in games:
                message += (
                    f"🎮 **{game['title']}**\n"
                    f"{game['description']}\n"
                    f"📅 Gratis dari {game['start_date']} hingga {game['end_date']}\n\n"
                )
            await ctx.send(message)
        else:
            await ctx.send("⚠️ Tidak ada game gratis yang tersedia saat ini.")

    @tasks.loop(minutes=60)
    async def start_notifier(self):
        """Loop tugas untuk pemberitahuan otomatis."""
        if not self.epic_channel_id:
            return

        channel = self.bot.get_channel(self.epic_channel_id)
        if not channel:
            return

        now = datetime.now(timezone.utc)
        if now.weekday() == 0:  # 0 = Senin
            games = self.get_free_games()
            if games:
                message = "**Game Gratis Minggu Ini di Epic Games:**\n"
                for game in games:
                    message += (
                        f"🎮 **{game['title']}**\n"
                        f"{game['description']}\n"
                        f"📅 Gratis dari {game['start_date']} hingga {game['end_date']}\n\n"
                    )
                await channel.send(message)
            else:
                await channel.send("⚠️ Tidak ada game gratis minggu ini di Epic Games Store.")

        if now.weekday() == 5:  # 5 = Sabtu
            await channel.send("⚠️ **Jangan lupa klaim game gratis di Epic Games!** Periode gratis akan segera berakhir.")

    def get_free_games(self):
        """Ambil data game gratis dari Epic Games Store API."""
        url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        try:
            response = requests.get(url)
            if response.status_code != 200:
                return []

            data = response.json()
            games = []

            for game in data["data"]["Catalog"]["searchStore"]["elements"]:
                if game.get("promotions") and game["promotions"].get("promotionalOffers"):
                    offers = game["promotions"]["promotionalOffers"][0]["promotionalOffers"]
                    for offer in offers:
                        discount = offer.get("discountSetting", {}).get("discountPercentage", 100)
                        if discount == 0:
                            start_date = offer["startDate"]
                            end_date = offer["endDate"]
                            if datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ") > datetime.utcnow():
                                games.append({
                                    "title": game["title"],
                                    "description": game.get("description", "Tidak ada deskripsi."),
                                    "start_date": datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d %B %Y"),
                                    "end_date": datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d %B %Y"),
                                })
            return games
        except Exception as e:
            print(f"Error saat mengambil data dari API: {e}")
            return []

def setup(bot):
    bot.add_cog(EpicGamesNotifier(bot))
