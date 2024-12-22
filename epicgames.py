import nextcord
from nextcord.ext import commands, tasks
import requests
from datetime import datetime, timezone, timedelta

class EpicGamesNotifier(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.epic_channel_id = None
        self.start_notifier.start()
        self.total_announcements = 0

    @commands.command(name="setepicgames")
    async def set_epic_games_channel(self, ctx, channel: nextcord.TextChannel):
        """Set channel untuk pemberitahuan game gratis Epic Games."""
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ Saya tidak memiliki izin untuk mengirim pesan ke {channel.mention}.")
            return

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

    @commands.command(name="setepicinterval")
    async def set_epic_interval(self, ctx, hours: int):
        """Atur interval pemberitahuan Epic Games"""

        if hours < 1:
            await ctx.send("❌ Interval minimal adalah 1 jam.")
            return
        
        self.start_notifier.change_interval(hours=hours)
        await ctx.send(f"✅ Interval pemberitahuan diatur ke setiap {hours} jam.")

    @commands.command(name="scheduleepic")
    async def schedule_epic(self, ctx, time: str):
        """Menjadwalkan pesan game Epic Games"""

        try:
            target_time = datetime.strptime(time, "%H:%M").time()
            now = datetime.now().time()

            if target_time < now:
                await ctx.send("❌ Waktu tidak valid. Pastikan waktu di masa mendatang.")
                return
            
            self.scheduled_time = target_time
            await ctx.send(f"✅ Pesan akan dikirim setiap hari pada pukul {time}.")
        except ValueError:
            await ctx.send("❌ Format waktu salah. Gunakan format HH:MM.")

    @commands.command(name="setepicdm")
    async def set_epic_dm(self, ctx, user: nextcord.User):
        """Set user untuk pemberitahuan game grais Epic Games via DM"""
        if not isinstance(user, nextcord.User):
            await ctx.send("❌ Anda harus mencantumkan pengguna yang valid.")
            return
        
        try:
            test_message = "✅ Anda telah diatur untuk menerima pemberitahuan Epic Games melalui DM."
            await user.send(test_message)

            self.epic_dm_user_id = user.id
            await ctx.send(f"✅ Pemberitahuan Epic Games akan dikirimkan ke {user.mention}.")

        except nextcord.Forbidden:
            await ctx.send(f"❌ Tidak dapat mengirim pesan ke {user.mention}. Pastikan DM Anda terbuka.")

    @commands.command(name="epicstats")
    async def epic_stats(self, ctx):
        """Lihat statistik pemberitahuan Epic Games"""
        await ctx.send(f"📊 Total game gratis yang diumumkan sejauh ini: {self.total_announcements}")

    @commands.command(name="search")
    async def search_game(self, ctx, *, game_name: str):
        """Mencari informasi game di Epic Games Store"""
        url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                await ctx.send(f"❌ Error: Tidak dapat mengakses API Epic Games (status {response.status_code}).")
                return
            
            data = response.json()
            games =  data["data"]["Catalog"]["searchStore"]["elements"]

            found_game = None
            for game in games:
                if game_name.lower() in game["title"].lower():
                    found_game = game
                    break

            if not found_game:
                await ctx.send(f"⚠️ Game dengan nama **{game_name}** tidak ditemukan di Epic Games Store.")
                return
            
            title = found_game["title"]
            description = found_game.get("description", "Tidak ada deskripsi yang tersedia.")
            price =  "Gratis" if "promotions" in found_game and found_game["promotions"].get("promotionalOffers") else "Harga tidak tersedia"
            store_link = f"https://store.epicgames.com/p/{title.replace(' ', '-').lower()}"

            message = (
                f"🎮 **{title}**\n"
                f"{description}\n"
                f"💰 Harga: {price}\n"
                f"🔗 [Lihat di Store]({store_link})"
            )
            await ctx.send(message)

        except Exception as e:
            print(f"Error saat mencari game: {e}")
            await ctx.send("❌ Terjadi kesalahan saat mencari game. Coba lagi nanti.")

    @tasks.loop(hours=24)
    async def start_notifier(self):
        """Loop tugas untuk pemberitahuan otomatis."""

        if games:
            self.total_announcements += len(games)
        if not self.epic_channel_id:
            return

        channel = self.bot.get_channel(self.epic_channel_id)
        if not channel:
            return

        now = datetime.now(timezone.utc).date()
        games = self.get_free_games()

        new_release_message = " "
        free_games_message = " "

        for game in games:
            release_date = datetime.strptime(game["start_date"], "%d %B %Y").date()
            end_date = datetime.strptime(game["end_date"], "%d %B %Y").date()

            if release_date == now and game["title"] not in self.released_games:
                new_release_message += (
                    f"🎉 **Game Baru Dirilis di Epic Games!**\n"
                    f"🎮 **{game['title']}**\n"
                    f"{game['description']}\n"
                    f"📅 Gratis mulai hari ini: {game['start_date']} hingga {game['end_date']}\n\n"
                    f"🔗 [Klaim Sekarang](https://store.epicgames.com/p/{game['title'].replace(' ', '-').lower()})\n\n"
                )
                self.released_games.add(game["title"])
            
            if end_date - now == timedelta(days=1):
                message += (
                    f"⚠️ **Jangan lupa klaim game gratis berikut di Epic Games!**\n"
                    f"🎮 **{game['title']}**\n"
                    f"{game['description']}\n"
                    f"📅 Gratis hingga {game['end_date']}\n\n"
                    f"🔗 [Klaim Sekarang](https://store.epicgames.com/p/{game['title'].replace(' ', '-').lower()})\n\n"
                    )
            elif end_date == now:
                message += (
                    f"🚨 **Hari ini adalah hari terakhir untuk klaim game gratis!**\n"
                    f"🎮 **{game['title']}**\n"
                    f"{game['description']}\n"
                    f"📅 Gratis hingga hari ini: {game['end_date']}\n\n"
                    f"🔗 [Klaim Sekarang](https://store.epicgames.com/p/{game['title'].replace(' ', '-').lower()})\n\n"
                )

        if new_release_message:
            await channel.send(new_release_message)

        if free_games_message:
            await channel.send(free_games_message)

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