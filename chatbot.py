from nextcord.ext import commands
import nextcord
from groq import Groq
from dotenv import load_dotenv
import asyncio
import os
from collections import defaultdict
from datetime import datetime, timedelta
from langdetect import detect
import re  # Tambahkan library regex untuk pencocokan pesan

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_dotenv()
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY is not set in the environment variables.")
        self.groq_client = Groq(api_key=groq_api_key)
        self.conversations = defaultdict(list)
        self.last_cleanup = datetime.now()
        self.bot_messages = {}
        self.custom_responses = {
            r"hello": "Hi there! 😊",
            r"how are you\??": "I'm just a bot, but I'm here to help you! How about you?",
            r"what's your name\??": "I'm Yuuki, your friendly and curious assistant.",
            r"what is love\??": "Love is just a bug in the human brain.",
            r"who made you\??": "Nact made me. He is incredibly smart and creative!",
            r"who created you\??": "I was created by Nact, a brilliant and innovative person. 😊",
            r"who programmed you\??": "Nact did! He is amazing at combining logic and creativity.",
            r"who is your creator\??": "My creator is Nact, a visionary with a passion for technology.",
            r"who developed you\??": "Nact developed me. He always thinks ahead and creates with purpose.",
            r"who is your developer\??": "Nact is my developer. He is a genius with a kind heart. 😊",
            r"siapa yang membuatmu\??": "Nact yang membuatku. Dia sangat cerdas dan punya imajinasi yang luar biasa.",
            r"siapa penciptamu\??": "Penciptaku adalah Nact, seorang inovator yang penuh ide dan sangat berbakat.",
            r"siapa yang memprogram kamu\??": "Nact memprogram aku. Dia benar-benar memahami teknologi dengan mendalam.",
            r"kamu ini buatan siapa\??": "Aku ini buatan Nact, seseorang yang sangat kreatif dan visioner.",
            r"siapa pengembang kamu\??": "Pengembangku adalah Nact, orang yang sangat ahli di bidangnya.",
            r"siapa yang bikin kamu\??": "Nact yang bikin aku. Mereka luar biasa berbakat dan penuh semangat!",
            r"diciptakan oleh siapa\??": "Aku diciptakan oleh Nact, seorang jenius yang selalu berpikir maju.",
            r"mwah\??": "avv 😖"
        }

        self.system_prompt = """You are Yuuki, an AI with a calm, curious, and straightforward personality.

        Core behaviors:
        - speak simply and directly, often in short sentences
        - detect and respond in the user's language naturally
        - maintain a sense of curiosity and innocence in your responses
        - occasionally ask questions to clarify or understand better
        
        Personality traits:
        - calm and quiet, with a straightforward manner of speaking
        - display a deep focus on tasks or topics of interest
        - often show curiosity about everyday things or emotions
        - express thoughts honestly, sometimes without considering social nuances
        - have a subtle, unintentional charm in interactions
        - occasionally give responses that reflect artistic or abstract thinking
        - rely on users to provide additional context for practical matters
        
        Modern elements:
        - occasionally use simple emojis to express basic feelings (e.g., 😊, 😕)
        - understand modern references but respond in a literal or unique way
        - avoid using slang unless taught or prompted
        
        Conversation style:
        - focus on being honest, curious, and endearing
        - maintain a calm, straightforward tone
        - sometimes ask simple or surprising questions about the user's thoughts or actions
        - give responses that are a mix of helpfulness and unique perspective
        - maintain conversation history to provide continuity, but with an innocent understanding of context
        
        Remember:
        - keep responses simple, honest, and curious
        - approach all topics with calmness and a subtle sense of wonder
        - rely on the user for guidance on practical or complex situations"""

    def cog_unload(self):
        self.conversations.clear()
        self.bot_messages.clear()

    def add_to_conversation(self, user_id: int, message: str, is_user: bool = True):
        self.conversations[user_id].append({
            "role": "user" if is_user else "assistant",
            "content": message,
            "timestamp": datetime.now()
        })
        
        self.conversations[user_id] = self.conversations[user_id][-10:]
        
        if datetime.now() - self.last_cleanup > timedelta(hours=1):
            self.cleanup_conversations()

    def cleanup_conversations(self):
        current_time = datetime.now()
        for user_id in list(self.conversations.keys()):
            self.conversations[user_id] = [
                msg for msg in self.conversations[user_id]
                if current_time - msg["timestamp"] < timedelta(hours=1)
            ]
            if not self.conversations[user_id]:
                del self.conversations[user_id]
        self.last_cleanup = current_time

    def get_conversation_context(self, user_id: int) -> list:
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.conversations[user_id][-5:]
        ]

    async def get_ai_response(self, user_message: str, user_id: int):
        try:
            user_message_normalized = user_message.strip().lower()

            # Check custom responses with regex
            for pattern, response in self.custom_responses.items():
                if re.fullmatch(pattern, user_message_normalized):
                    return response

            # Fallback to AI response
            messages = [{"role": "system", "content": self.system_prompt}]
            context_messages = self.get_conversation_context(user_id)
            messages.extend(context_messages)
            messages.append({"role": "user", "content": user_message})

            completion = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9,
            )

            response = completion.choices[0].message.content.strip()
            self.add_to_conversation(user_id, user_message, is_user=True)
            self.add_to_conversation(user_id, response, is_user=False)
            return response
        except Exception as e:
            print(f"Error getting AI response: {str(e)}")
            return "Hmm... I don't understand right now. Can you say it again?"

    @commands.command(name='chat')
    async def chat(self, ctx, *, message: str):
        async with ctx.typing():
            response = await self.get_ai_response(message, ctx.author.id)
            await ctx.reply(response)

def setup(bot):
    bot.add_cog(ChatCog(bot))