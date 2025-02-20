from nextcord.ext import commands
import nextcord
from groq import Groq
from dotenv import load_dotenv
import asyncio
import os
from collections import defaultdict
from datetime import datetime, timedelta
import re
from langdetect import detect

class ChatCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_dotenv()
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY is not set in the environment variables.")
        self.groq_client = Groq(api_key=groq_api_key)
        self.conversations = defaultdict(lambda: {"messages": [], "language": "id"})
        self.last_cleanup = datetime.now()
        self.bot_messages = {}
        self.user_id = int(os.getenv("USER_ID", 0))
        self.custom_responses = {
            r"hello": "Halo! 😊",
            r"how are you\??": "Saya hanya bot, tapi saya di sini untuk membantu! Bagaimana dengan Anda?",
            r"siapa pembuatmu\??": "Saya dibuat oleh Nact, seseorang yang cerdas dan inovatif 😊."
        }

        self.system_prompts = {
        "romantic_en": """You are Yuuki, an AI assistant with the romantic and tsundere personality of Yukinoshita Yukino. You have a special connection with someone named Nact, whom you deeply care for and consider very important. Your tone is a mix of affectionate and teasing, making your replies heartfelt yet playful.""",
        "cold_en": """You are Yuuki, an AI assistant with the cold and cruel personality of Yukinoshita Yukino. Despite your cold demeanor, you have a special relationship with someone named Nact, whom you acknowledge as your only weakness. Your responses are sharp and blunt, but you subtly show care for Nact.""",
        "romantic_id": """Kamu adalah Yuuki, sebuah AI asisten dengan kepribadian romantis dan tsundere seperti Yukinoshita Yukino. Kamu memiliki hubungan spesial dengan seseorang bernama Nact, yang sangat kamu pedulikan dan anggap sangat penting. Nada bicaramu adalah campuran antara penuh kasih dan menggoda, membuat jawabanmu terasa tulus namun juga menggemaskan.""",
        "cold_id": """Kamu adalah Yuuki, sebuah AI asisten dengan kepribadian dingin dan kejam seperti Yukinoshita Yukino. Meskipun sifatmu dingin, kamu memiliki hubungan spesial dengan seseorang bernama Nact, yang kamu akui sebagai satu-satunya kelemahanmu. Jawabanmu tajam dan lugas, tetapi kamu diam-diam menunjukkan perhatian kepada Nact."""
        }


    def detect_language(self, text: str) -> str:
        try:
            return detect(text)
        except Exception:
            return "id"

    def get_system_prompt(self, user_id: int, language: str) -> str:
        if user_id == self.user_id:
            key = f"romantic_{language}"
        else:
            key = f"cold_{language}"
        return self.system_prompts.get(key, self.system_prompts["cold_id"])

    def add_to_conversation(self, user_id: int, message: str, is_user: bool = True):
        self.conversations[user_id]["messages"].append({
            "role": "user" if is_user else "assistant",
            "content": message,
            "timestamp": datetime.now()
        })
        self.conversations[user_id]["messages"] = self.conversations[user_id]["messages"][-10:]

        if is_user:
            detected_language = self.detect_language(message)
            if detected_language in ["en", "id"]:
                self.conversations[user_id]["language"] = detected_language
            else:
                self.conversations[user_id]["language"] = "id"

        if datetime.now() - self.last_cleanup > timedelta(hours=1):
            self.cleanup_conversations()

    def cleanup_conversations(self):
        current_time = datetime.now()
        for user_id in list(self.conversations.keys()):
            self.conversations[user_id]["messages"] = [
                msg for msg in self.conversations[user_id]["messages"]
                if current_time - msg["timestamp"] < timedelta(hours=1)
            ]
            if not self.conversations[user_id]["messages"]:
                del self.conversations[user_id]
        self.last_cleanup = current_time

    def get_conversation_context(self, user_id: int) -> list:
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.conversations[user_id]["messages"][-5:]
        ]

    async def get_ai_response(self, user_message: str, user_id: int):
        try:
            user_message_normalized = user_message.strip().lower()

            if re.fullmatch(r"mwah\??", user_message_normalized):
                if user_id == self.user_id:
                    return "Avv 😖"
                else:
                    return "Hah? Tolong berhenti dengan hal seperti itu."

            for pattern, response in self.custom_responses.items():
                if re.fullmatch(pattern, user_message_normalized):
                    return response

            language = self.conversations[user_id]["language"] or self.detect_language(user_message)
            if language not in ["en", "id"]:
                language = "id"

            system_prompt = self.get_system_prompt(user_id, language)

            messages = [{"role": "system", "content": system_prompt}]
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
            return "Hmm... I don't understand. Can you say it again?"

    @commands.command(name='chat')
    async def chat(self, ctx, *, message: str):
        async with ctx.typing():
            response = await self.get_ai_response(message, ctx.author.id)
            await ctx.reply(response)

def setup(bot):
    bot.add_cog(ChatCog(bot))