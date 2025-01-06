import requests
from nextcord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

class URLShortener(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("CUTTLY_API_KEY")
        self.base_url = "https://cutt.ly/api/api.php"

    def shorten_link(self, full_link):
        """Shorten URL using the Cutt.ly API."""
        if not self.api_key:
            return "Error: Cutt.ly API key not found. Ensure it is set in the .env file."

        payload = {"key": self.api_key, "short": full_link}
        response = requests.get(self.base_url, params=payload)
        data = response.json()

        try:
            title = data["url"]["title"]
            short_link = data["url"]["shortLink"]
            return f"Title: {title}\nLink: {short_link}"
        except:
            status = data["url"]["status"]
            return f"Error Status: {status}"

    @commands.command(name="short")
    async def shorten_command(self, ctx, link: str):
        """Command to shorten a URL."""
        result = self.shorten_link(link)
        await ctx.send(result)

def setup(bot):
    bot.add_cog(URLShortener(bot))