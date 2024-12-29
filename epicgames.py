import nextcord
from nextcord.ext import commands, tasks
import requests
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

class EpicGamesNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.epic_channel_id = None
        self.scheduled_time = None
        self.total_announcements = 0
        self.start_notifier.start()

    def is_admin_or_owner(self, ctx):
        """Cek apakah pengguna adalah admin atau pemilik bot."""
        user_id = os.getenv("USER_ID")
        return ctx.author.guild_permissions.administrator or str(ctx.author.id) == user_id

    @commands.command(name="searchepic")
    async def search_epic(self, ctx, *, game_name):
        """Cari game di Epic Games Store berdasarkan nama."""
        games = self.search_epic_games(game_name)
        if games:
            message = "**Hasil Pencarian di Epic Games Store:**\n"
            for game in games[:5]:
                message += (
                    f"🎮 **{game['title']}**\n"
                    f"{game['description']}\n"
                    f"💸 Harga: {game['price']}\n"
                    f"🔗 [Link ke Epic Store]({game['url']})\n\n"
                )
            await ctx.send(message)
        else:
            await ctx.send("❌ Tidak ada hasil yang ditemukan untuk pencarian tersebut.")

    def search_epic_games(self, game_name):
        """Mencari game di Epic Games Store berdasarkan nama."""
        url = "https://store.epicgames.com/api/content/v2/catalog"
        params = {
            "keywords": game_name,
            "category": "games",
            "locale": "en-US",
            "count": 10,
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code != 200:
                print(f"Error: API mengembalikan status {response.status_code}")
                return []

            data = response.json()
            games = []

            for element in data.get("elements", []):
                title = element.get("title", "Unknown")
                description = element.get("description", "Tidak ada deskripsi.")
                price_info = element.get("price", {}).get("totalPrice", {}).get("fmtPrice", {})
                price = price_info.get("originalPrice", "Tidak diketahui")
                games.append({
                    "title": title,
                    "description": description,
                    "price": price,
                    "url": f"https://store.epicgames.com/p/{title.replace(' ', '-').lower()}",
                })

            return games
        except requests.RequestException as e:
            print(f"Error saat mengambil data dari API: {e}")
            return []

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
                    f"📅 Gratis dari {game['start_date']} hingga {game['end_date']}\n"
                    f"🔗 [Klaim Sekarang](https://store.epicgames.com/p/{game['title'].replace(' ', '-').lower()})\n\n"
                )
            await ctx.send(message)
        else:
            await ctx.send("⚠️ Tidak ada game gratis yang tersedia saat ini.")

    @commands.command(name="setepicgames")
    async def set_epic_games_channel(self, ctx, channel: nextcord.TextChannel):
        """Set channel untuk pemberitahuan game gratis Epic Games."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ Anda tidak memiliki izin untuk menggunakan perintah ini.")
            return

        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ Saya tidak memiliki izin untuk mengirim pesan ke {channel.mention}.")
            return

        self.epic_channel_id = channel.id
        await ctx.send(f"✅ Channel Epic Games Notifications telah diatur ke {channel.mention}")

    @commands.command(name="scheduleepic")
    async def schedule_epic(self, ctx, time: str):
        """Menjadwalkan pesan game Epic Games."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ Anda tidak memiliki izin untuk menggunakan perintah ini.")
            return
        
        try:
            target_time = datetime.strptime(time, "%H:%M").time()
            now = datetime.now().time()

            if target_time < now:
                await ctx.send("❌ Waktu tidak valid. Pastikan waktu di masa mendatang.")
                return
            
            self.scheduled_time = target_time
            await ctx.send(f"✅ Pesan pemberitahuan akan dikirim setiap hari pada pukul {time}.")
        except ValueError:
            await ctx.send("❌ Format waktu salah. Gunakan format HH:MM.")

    @tasks.loop(minutes=1)
    async def start_notifier(self):
        """Loop tugas untuk pemberitahuan otomatis."""
        if self.scheduled_time and datetime.now().time().hour == self.scheduled_time.hour and datetime.now().time().minute == self.scheduled_time.minute:
            if self.epic_channel_id:
                channel = self.bot.get_channel(self.epic_channel_id)
                if channel:
                    games = self.get_free_games()
                    if games:
                        message = "**Game Gratis di Epic Games Saat Ini:**\n"
                        for game in games:
                            message += (
                                f"🎮 **{game['title']}**\n"
                                f"{game['description']}\n"
                                f"📅 Gratis dari {game['start_date']} hingga {game['end_date']}\n"
                                f"🔗 [Klaim Sekarang](https://store.epicgames.com/p/{game['title'].replace(' ', '-').lower()})\n\n"
                            )
                        await channel.send(message)

    def get_free_games(self):
        """Ambil data game gratis dari Epic Games Store API."""
        url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Error: API mengembalikan status {response.status_code}")
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