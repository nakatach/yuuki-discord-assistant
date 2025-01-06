import nextcord
from nextcord.ext import commands, tasks
import requests
from datetime import datetime, timedelta
import pytz
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TIMEZONE = pytz.timezone("Asia/Jakarta")

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
                logger.info("Weather configuration successfully loaded")
        except FileNotFoundError:
            logger.info("Configuration file not found, creating a new one")
            self.save_config()

    def save_config(self):
        with open('weather_config.json', 'w') as f:
            json.dump(self.weather_config, f, indent=4)
            logger.info("Weather configuration successfully saved")

    async def get_coordinates(self, city):
        """Get coordinates from a city name"""
        try:
            geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en"
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
            logger.error(f"Error during geocoding: {e}")
            return None

    def get_weather_description(self, code):
        """Convert weather code to English description"""
        weather_codes = {
            0: "Clear",
            1: "Partly Cloudy",
            2: "Cloudy",
            3: "Overcast",
            45: "Foggy",
            48: "Dense Fog",
            51: "Light Drizzle",
            53: "Moderate Drizzle",
            55: "Heavy Drizzle",
            61: "Light Rain",
            63: "Moderate Rain",
            65: "Heavy Rain",
            80: "Local Showers",
            95: "Thunderstorm"
        }
        return weather_codes.get(code, "Unknown")

    async def get_weather(self, city):
        try:
            location = await self.get_coordinates(city)
            if not location:
                return "❌ City not found"

            weather_url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={location['lat']}"
                f"&longitude={location['lon']}"
                f"&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
                f"&current_weather=true"
                f"&timezone=auto"
            )
            
            response = requests.get(weather_url)
            response.raise_for_status()
            weather_data = response.json()
            
            current = weather_data['current_weather']
            daily = weather_data['daily']
            
            weather_message = (
                f"🌦️ **Weather Forecast for {location['name']}** 🌦️\n"
                f"*{datetime.now(TIMEZONE).strftime('%d %B %Y')}*\n\n"
                f"**Current Conditions:**\n"
                f"• Temperature: {current['temperature']}°C\n"
                f"• Wind Speed: {current['windspeed']} km/h\n\n"
                f"**Today's Forecast:**\n"
                f"• Conditions: {self.get_weather_description(daily['weather_code'][0])}\n"
                f"• High: {daily['temperature_2m_max'][0]}°C\n"
                f"• Low: {daily['temperature_2m_min'][0]}°C\n"
                f"• Rain Probability: {daily['precipitation_probability_max'][0]}%\n\n"
                f"**Weather Tips:**\n"
            )
            
            weather_code = daily['weather_code'][0]
            rain_prob = daily['precipitation_probability_max'][0]
            
            if rain_prob > 70:
                weather_message += "🌂 Don't forget to bring an umbrella! High chance of rain today.\n"
            elif rain_prob > 30:
                weather_message += "🌂 There's a chance of rain, better to have an umbrella just in case.\n"
            
            if weather_code in [0, 1]:
                weather_message += "🧴 It's sunny, don't forget to wear sunscreen!\n"
            elif weather_code in [45, 48]:
                weather_message += "⚠️ Drive carefully, visibility might be limited.\n"
            elif weather_code in [95]:
                weather_message += "⚡ Be cautious of thunderstorms! Avoid outdoor activities.\n"
            
            return weather_message
            
        except Exception as e:
            logger.error(f"Error while fetching weather data: {e}")
            return "❌ Sorry, an error occurred while fetching weather data"

    @tasks.loop(minutes=1)
    async def weather_check(self):
        now = datetime.now(TIMEZONE)
        current_time = now.strftime("%H:%M")
        
        for guild_id, config in self.weather_config.items():
            if config.get("enabled", False) and config.get("time") == current_time:
                channel = self.bot.get_channel(config["channel_id"])
                if channel:
                    weather_report = await self.get_weather(config["city"])
                    try:
                        await channel.send(weather_report)
                        logger.info(f"Successfully sent weather forecast to channel {channel.id}")
                    except Exception as e:
                        logger.error(f"Failed to send weather forecast: {e}")

    @weather_check.before_loop
    async def before_weather_check(self):
        await self.bot.wait_until_ready()

    @commands.command(name="setw")
    async def set_weather(self, ctx, channel: nextcord.TextChannel, city: str, time: str):
        """
        Set channel, city, and time for daily weather forecasts
        Example: !setw #weather-updates Jakarta 07:00
        """
        try:
            datetime.strptime(time, "%H:%M")
            
            location = await self.get_coordinates(city)
            if not location:
                await ctx.send("❌ City not found!")
                return
                
            self.weather_config[str(ctx.guild.id)] = {
                "channel_id": channel.id,
                "city": city,
                "time": time,
                "enabled": True
            }
            
            self.save_config()
            
            weather_report = await self.get_weather(city)
            await ctx.send(f"✅ Successfully set up the weather forecast!\n"
                         f"📍 City: {location['name']}\n"
                         f"⏰ Time: {time}\n"
                         f"📢 Channel: {channel.mention}\n\n"
                         f"Here's an example of the forecast that will be sent:\n{weather_report}")
                
        except ValueError:
            await ctx.send("❌ Invalid time format! Use 24-hour format (HH:MM)")
        except Exception as e:
            await ctx.send(f"❌ An error occurred: {str(e)}")

    @commands.command(name="stopw")
    @commands.has_permissions(administrator=True)
    async def stop_weather(self, ctx):
        """Stop daily weather forecasts"""
        guild_id = str(ctx.guild.id)
        if guild_id in self.weather_config:
            self.weather_config[guild_id]["enabled"] = False
            self.save_config()
            await ctx.send("✅ Daily weather forecasts have been disabled")
        else:
            await ctx.send("❌ Weather forecasts are not set up for this server")

    @commands.command(name="startw")
    @commands.has_permissions(administrator=True)
    async def start_weather(self, ctx):
        """Resume daily weather forecasts"""
        guild_id = str(ctx.guild.id)
        if guild_id in self.weather_config:
            self.weather_config[guild_id]["enabled"] = True
            self.save_config()
            await ctx.send("✅ Daily weather forecasts have been enabled")
        else:
            await ctx.send("❌ Weather forecasts are not set up for this server")

    @commands.command(name="checkw")
    async def check_weather(self, ctx, *, city: str = None):
        """Check the current weather for a specific city"""
        if not city:
            guild_id = str(ctx.guild.id)
            if guild_id in self.weather_config:
                city = self.weather_config[guild_id]["city"]
            else:
                await ctx.send("❌ Please provide a city name!")
                return

        weather_report = await self.get_weather(city)
        await ctx.send(weather_report)

def setup(bot):
    bot.add_cog(Weather(bot))