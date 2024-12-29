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
        """Cek apakah pengguna adalah admin atau pemilik bot."""
        user_id = os.getenv("USER_ID")
        return ctx.author.guild_permissions.administrator or str(ctx.author.id) == user_id

    @commands.command(name="searchsteam")
    async def search_steam(self, ctx, *args):
        """Cari game di Steam berdasarkan nama dan harga (opsional)."""
        if len(args) == 1 and args[0].isdigit():
            max_price = int(args[0])
            games = self.search_steam_games(max_price=max_price)
        else:
            game_name = " ".join(args)
            games = self.search_steam_games(game_name=game_name)
        
        if games:
            message = "**Hasil Pencarian di Steam:**\n"
            for game in games[:10]:
                message += (
                    f"🎮 **{game['name']}**\n"
                    f"💸 Harga: {game['price']}\n"
                    f"🔗 [Link ke Steam Store]({game['url']})\n\n"
                )
            await ctx.send(message)
        else:
            await ctx.send("❌ Tidak ada hasil yang ditemukan untuk pencarian tersebut.")

    @commands.command(name="setsteamprice")
    async def set_steam_price(self, ctx, price: int):
        """Set batas harga maksimum (dalam Rupiah) untuk notifikasi diskon game."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ Anda tidak memiliki izin untuk menggunakan perintah ini.")
            return

        if price < 0:
            await ctx.send("❌ Harga tidak valid.")
            return

        self.steam_price_limit = price
        await ctx.send(f"✅ Harga maksimum untuk notifikasi diskon diatur ke Rp {price:,}.")

    @commands.command(name="setsteam")
    async def set_steam_channel(self, ctx, channel: nextcord.TextChannel):
        """Set channel untuk pemberitahuan diskon Steam."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ Anda tidak memiliki izin untuk menggunakan perintah ini.")
            return

        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ Saya tidak memiliki izin untuk mengirim pesan ke {channel.mention}.")
            return

        self.steam_channel_id = channel.id
        await ctx.send(f"✅ Channel Steam Notifications telah diatur ke {channel.mention}.")

    @commands.command(name="schedulesteam")
    async def schedule_steam(self, ctx, time_str: str):
        """Menjadwalkan jam pengiriman notifikasi diskon Steam setiap hari."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ Anda tidak memiliki izin untuk menggunakan perintah ini.")
            return

        try:
            target_time = datetime.strptime(time_str, "%H:%M").time()
            self.scheduled_time = target_time
            await ctx.send(f"✅ Notifikasi diskon Steam akan dikirim setiap hari pada pukul {time_str}.")
        except ValueError:
            await ctx.send("❌ Format waktu salah. Gunakan format HH:MM.")

    @commands.command(name="stopsteam")
    async def stop_steam(self, ctx):
        """Hentikan notifikasi diskon Steam harian."""
        if not self.is_admin_or_owner(ctx):
            await ctx.send("❌ Anda tidak memiliki izin untuk menggunakan perintah ini.")
            return

        self.scheduled_time = None
        await ctx.send("✅ Notifikasi diskon Steam harian telah dihentikan.")

    @tasks.loop(minutes=1)
    async def start_notifier(self):
        """Loop tugas untuk pemberitahuan otomatis."""
        if self.scheduled_time and datetime.now().time().hour == self.scheduled_time.hour and datetime.now().time().minute == self.scheduled_time.minute:
            if self.steam_channel_id and self.steam_price_limit:
                channel = self.bot.get_channel(self.steam_channel_id)
                if channel:
                    games = self.get_discounted_games()
                    if games:
                        message = "**Game Diskon di Steam di Bawah Harga Maksimum:**\n"
                        for game in games:
                            message += (
                                f"🎮 **{game['name']}**\n"
                                f"💸 Harga setelah diskon: Rp {game['price']:,}\n"
                                f"🔗 [Link ke Steam Store]({game['url']})\n\n"
                            )
                        await channel.send(message)

    def search_steam_games(self, game_name=None, max_price=None):
        """Mencari game di Steam berdasarkan nama dan harga (opsional)."""
        url = f"https://store.steampowered.com/api/storesearch/?term={game_name}&cc=ID&l=indonesian"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Error: API Steam mengembalikan status {response.status_code}")
                return []

            data = response.json()
            games = []

            for game in data.get("items", []):
                price_data = game.get("price", {})
                if isinstance(price_data, dict):
                    initial_price = price_data.get("initial", 0) / 100
                    final_price = price_data.get("final", 0) / 100
                    price = f"Rp {int(final_price):,}" if final_price else "Gratis"
                else:
                    price = "Gratis" if price_data == 0 else f"Rp {int(price_data) / 100:,}"

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
            print(f"Error saat mengambil data dari API Steam: {e}")
            return []

    def get_discounted_games(self):
        """Ambil daftar game dengan diskon di bawah harga maksimum."""
        url = "https://store.steampowered.com/api/featuredcategories/?cc=ID&l=indonesian"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Error: API Steam mengembalikan status {response.status_code}")
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
            print(f"Error saat mengambil data dari API Steam: {e}")
            return []

def setup(bot):
    bot.add_cog(SteamNotifier(bot))