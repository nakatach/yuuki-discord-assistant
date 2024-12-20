import nextcord
import asyncio
import yt_dlp
from nextcord.ext import commands

class MusicPlayer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.queue = {}
        self.is_playing = {}
        self.yt_dlp_options = {"format": "bestaudio/best"}
        self.ytdl = yt_dlp.YoutubeDL(self.yt_dlp_options)
        self.ffmpeg_options = {'options': '-vn -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'}

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'{self.bot.user} is now jamming')

    def search_youtube(self, query):
        try:
            result = self.ytdl.extract_info(f"ytsearch:{query}", download=False)
            video = result['entries'][0]  # Ambil hasil pertama dari pencarian
            return video['webpage_url'], video['title']
        except Exception as e:
            print(f"Error searching on YouTube: {e}")
            return None, None

    async def play_next(self, ctx):
        if len(self.queue[ctx.guild.id]) > 0:
            url, title = self.queue[ctx.guild.id].pop(0)
            await self.play_song(ctx, url, title)
        else:
            self.is_playing[ctx.guild.id] = False

    async def play_song(self, ctx, url, title):
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=False))

            song = data['url']
            print(f"Playing song: {song}")
            player = nextcord.FFmpegPCMAudio(song, **self.ffmpeg_options)

            self.voice_clients[ctx.guild.id].play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), loop))
            await ctx.send(f"Now playing: {title}")
        except Exception as e:
            print(f"Error playing the song: {e}")
            await ctx.send("Error playing the song.")

    @commands.command(name="play")
    async def play(self, ctx, *, search: str):
        if not ctx.author.voice:
            await ctx.send("You need to be connected to a voice channel to play music.")
            return

        if ctx.guild.id not in self.queue:
            self.queue[ctx.guild.id] = []

        if ctx.guild.id not in self.is_playing:
            self.is_playing[ctx.guild.id] = False

        if ctx.guild.id not in self.voice_clients or not self.voice_clients[ctx.guild.id].is_connected():
            try:
                voice_client = await ctx.author.voice.channel.connect()
                self.voice_clients[voice_client.guild.id] = voice_client
                print("Connected to voice channel")
            except Exception as e:
                print(f"Error connecting to the voice channel: {e}")
                await ctx.send("Error connecting to the voice channel.")
                return

        if not search.startswith("http"):
            url, title = self.search_youtube(search)
            if url is None:
                await ctx.send("Could not find the song on YouTube.")
                return
        else:
            url = search
            title = "Playing from provided URL"

        self.queue[ctx.guild.id].append((url, title))
        await ctx.send(f"Added to queue: {title}")

        if not self.is_playing[ctx.guild.id]:
            self.is_playing[ctx.guild.id] = True
            await self.play_next(ctx)

    @commands.command(name="pause")
    async def pause(self, ctx):
        try:
            self.voice_clients[ctx.guild.id].pause()
        except Exception as e:
            print(e)

    @commands.command(name="resume")
    async def resume(self, ctx):
        try:
            self.voice_clients[ctx.guild.id].resume()
        except Exception as e:
            print(e)

    @commands.command(name="skip")
    async def skip(self, ctx):
        if ctx.guild.id in self.voice_clients:
            self.voice_clients[ctx.guild.id].stop()
            await self.play_next(ctx)

    @commands.command(name="stop")
    async def stop(self, ctx):
        try:
            self.voice_clients[ctx.guild.id].stop()
            await self.voice_clients[ctx.guild.id].disconnect()
            self.queue[ctx.guild.id] = []
            self.is_playing[ctx.guild.id] = False
        except Exception as e:
            print(e)

    @commands.command(name="q")
    async def show_queue(self, ctx):
        if ctx.guild.id in self.queue and self.queue[ctx.guild.id]:
            queue_str = "\n".join([f"{i+1}. {title}" for i, (_, title) in enumerate(self.queue[ctx.guild.id])])
            await ctx.send(f"Current queue:\n{queue_str}")
        else:
            await ctx.send("The queue is empty.")

    @commands.command(name="remove")
    async def remove(self, ctx, index: int):
        if ctx.guild.id in self.queue and len(self.queue[ctx.guild.id]) >= index > 0:
            removed_song = self.queue[ctx.guild.id].pop(index - 1)
            await ctx.send(f"Removed from queue: {removed_song[1]}")
        else:
            await ctx.send("Invalid index or empty queue.")

def setup(bot):
    bot.add_cog(MusicPlayer(bot))
