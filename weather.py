import nextcord
from nextcord.ext import commands, tasks
import requests
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Weather(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.weather_config = {}
        self.load_config()
        self.weather_check.start()
        
    def load_config(self):
        try:
            with open('weather_config.json', 'r') as f:
                self.weather_config = json.load(f)
                logger.info("Konfigurasi cuaca berhasil dimuat")
        except FileNotFoundError:
            logger.info("File konfigurasi tidak ditemukan, membuat baru")
            self.save_config()

    def save_config(self):
        with open('weather_config.json', 'w') as f:
            json.dump(self.weather_config, f, indent=4)
            logger.info("Konfigurasi cuaca berhasil disimpan")

    async def get_coordinates(self, city):
        """Mendapatkan koordinat dari nama kota"""
        try:
            geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=id"
            response = requests.get(geocoding_url)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('results'):
                return None
                
            location = data['results'][0]
            return {
                'lat': location['latitude'],
                'lon': location['longitude'],
                'name': location['name']
            }
        except Exception as e:
            logger.error(f"Error saat geocoding: {e}")
            return None

    def get_weather_description(self, code):
        """Mengkonversi kode cuaca ke deskripsi bahasa Indonesia"""
        weather_codes = {
            0: "Cerah",
            1: "Sebagian Berawan",
            2: "Berawan",
            3: "Mendung",
            45: "Berkabut",
            48: "Berkabut Tebal",
            51: "Gerimis Ringan",
            53: "Gerimis Sedang",
            55: "Gerimis Lebat",
            61: "Hujan Ringan",
            63: "Hujan Sedang",
            65: "Hujan Lebat",
            80: "Hujan Lokal",
            95: "Hujan Petir"
        }
        return weather_codes.get(code, "Tidak Diketahui")

    async def get_weather(self, city):
        try:
            location = await self.get_coordinates(city)
            if not location:
                return "❌ Kota tidak ditemukan"

            weather_url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={location['lat']}"
                f"&longitude={location['lon']}"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
                f"&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
                f"&timezone=auto"
            )
            
            response = requests.get(weather_url)
            response.raise_for_status()
            weather_data = response.json()
            
            current = weather_data['current']
            daily = weather_data['daily']
            
            # Buat pesan ramalan cuaca
            weather_message = (
                f"🌦️ **Ramalan Cuaca untuk {location['name']}** 🌦️\n"
                f"*{datetime.now().strftime('%d %B %Y')}*\n\n"
                f"**Kondisi Saat Ini:**\n"
                f"• Suhu: {current['temperature_2m']}°C\n"
                f"• Kelembapan: {current['relative_humidity_2m']}%\n"
                f"• Kecepatan Angin: {current['wind_speed_10m']} km/h\n\n"
                f"**Prakiraan Hari Ini:**\n"
                f"• Kondisi: {self.get_weather_description(daily['weather_code'][0])}\n"
                f"• Suhu Tertinggi: {daily['temperature_2m_max'][0]}°C\n"
                f"• Suhu Terendah: {daily['temperature_2m_min'][0]}°C\n"
                f"• Probabilitas Hujan: {daily['precipitation_probability_max'][0]}%\n\n"
                f"**Tips Cuaca:**\n"
            )
            
            # Tambahkan tips berdasarkan kondisi cuaca
            weather_code = daily['weather_code'][0]
            rain_prob = daily['precipitation_probability_max'][0]
            
            if rain_prob > 70:
                weather_message += "🌂 Jangan lupa bawa payung! Kemungkinan hujan tinggi hari ini.\n"
            elif rain_prob > 30:
                weather_message += "🌂 Ada kemungkinan hujan, siapkan payung untuk jaga-jaga.\n"
            
            if weather_code in [0, 1]:
                weather_message += "🧴 Cuaca cerah, jangan lupa pakai sunscreen!\n"
            elif weather_code in [45, 48]:
                weather_message += "⚠️ Hati-hati berkendara, jarak pandang mungkin terbatas.\n"
            elif weather_code in [95]:
                weather_message += "⚡ Waspada petir! Hindari beraktivitas di luar ruangan.\n"
            
            return weather_message
            
        except Exception as e:
            logger.error(f"Error saat mengambil data cuaca: {e}")
            return "❌ Maaf, terjadi kesalahan saat mengambil data cuaca"

    @tasks.loop(minutes=1)
    async def weather_check(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        for guild_id, config in self.weather_config.items():
            if config.get("enabled", False) and config.get("time") == current_time:
                channel = self.bot.get_channel(config["channel_id"])
                if channel:
                    weather_report = await self.get_weather(config["city"])
                    try:
                        await channel.send(weather_report)
                        logger.info(f"Berhasil mengirim ramalan cuaca ke channel {channel.id}")
                    except Exception as e:
                        logger.error(f"Gagal mengirim ramalan cuaca: {e}")

    @weather_check.before_loop
    async def before_weather_check(self):
        await self.bot.wait_until_ready()

    @commands.command(name="setweather")
    async def set_weather(self, ctx, channel: nextcord.TextChannel, city: str, time: str):
        """
        Mengatur channel, kota, dan waktu untuk ramalan cuaca harian
        Contoh: !setweather #ramalan-cuaca Jakarta 07:00
        """
        try:
            # Validasi format waktu
            datetime.strptime(time, "%H:%M")
            
            # Validasi kota
            location = await self.get_coordinates(city)
            if not location:
                await ctx.send("❌ Kota tidak ditemukan!")
                return
                
            self.weather_config[str(ctx.guild.id)] = {
                "channel_id": channel.id,
                "city": city,
                "time": time,
                "enabled": True
            }
            
            self.save_config()
            
            # Tampilkan contoh ramalan cuaca
            weather_report = await self.get_weather(city)
            await ctx.send(f"✅ Berhasil mengatur ramalan cuaca!\n"
                         f"📍 Kota: {location['name']}\n"
                         f"⏰ Waktu: {time}\n"
                         f"📢 Channel: {channel.mention}\n\n"
                         f"Berikut contoh ramalan cuaca yang akan dikirim:\n{weather_report}")
                
        except ValueError:
            await ctx.send("❌ Format waktu tidak valid! Gunakan format 24 jam (HH:MM)")
        except Exception as e:
            await ctx.send(f"❌ Terjadi kesalahan: {str(e)}")

    @commands.command(name="stopweather")
    @commands.has_permissions(administrator=True)
    async def stop_weather(self, ctx):
        """Menghentikan pengiriman ramalan cuaca harian"""
        guild_id = str(ctx.guild.id)
        if guild_id in self.weather_config:
            self.weather_config[guild_id]["enabled"] = False
            self.save_config()
            await ctx.send("✅ Ramalan cuaca harian telah dinonaktifkan")
        else:
            await ctx.send("❌ Ramalan cuaca belum diatur untuk server ini")

    @commands.command(name="startweather")
    @commands.has_permissions(administrator=True)
    async def start_weather(self, ctx):
        """Memulai kembali pengiriman ramalan cuaca harian"""
        guild_id = str(ctx.guild.id)
        if guild_id in self.weather_config:
            self.weather_config[guild_id]["enabled"] = True
            self.save_config()
            await ctx.send("✅ Ramalan cuaca harian telah diaktifkan")
        else:
            await ctx.send("❌ Ramalan cuaca belum diatur untuk server ini")

    @commands.command(name="checkweather")
    async def check_weather(self, ctx, *, city: str = None):
        """Mengecek cuaca saat ini untuk kota tertentu"""
        if not city:
            guild_id = str(ctx.guild.id)
            if guild_id in self.weather_config:
                city = self.weather_config[guild_id]["city"]
            else:
                await ctx.send("❌ Mohon masukkan nama kota!")
                return

        weather_report = await self.get_weather(city)
        await ctx.send(weather_report)

def setup(bot):
    bot.add_cog(Weather(bot))