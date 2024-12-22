import nextcord
from pytz import timezone
from nextcord.ext import commands, tasks
from datetime import datetime, timedelta
import re

class TaskReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tasks = []
        self.reminder_channel_id = None
        self.check_tasks.start()

    @commands.command(name="addtask")
    async def add_task(self, ctx, name: str, deadline: str):
        """
        Tambahkan tugas baru.
        Format: !addtask "Nama Tugas" "YYYY-MM-DD HH:MM" (Zona WIB)
        """
        try:
            if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", deadline):
                await ctx.send("❌ Format tanggal salah. Gunakan format **YYYY-MM-DD HH:MM** (Zona WIB).")
                return

            wib = timezone("Asia/Jakarta")
            parsed_time = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
            deadline_datetime = wib.localize(parsed_time)

            self.tasks.append({"name": name, "deadline": deadline_datetime, "notified": False, "completed": False})
            await ctx.send(f"✅ Tugas **{name}** berhasil ditambahkan dengan deadline **{deadline_datetime.strftime('%Y-%m-%d %H:%M')} WIB**.")
        except ValueError as e:
            await ctx.send(f"❌ Terjadi kesalahan pada parsing tanggal: {str(e)}")

    @commands.command(name="removetask")
    async def remove_task(self, ctx, name: str):
        """
        Hapus tugas berdasarkan nama.
        Format: !removetask "Nama Tugas"
        """
        for task in self.tasks:
            if task["name"].lower() == name.lower():
                self.tasks.remove(task)
                await ctx.send(f"✅ Tugas **{name}** berhasil dihapus.")
                return
        await ctx.send(f"❌ Tugas **{name}** tidak ditemukan.")

    @commands.command(name="listtasks")
    async def list_tasks(self, ctx):
        """
        Lihat daftar semua tugas yang terdaftar.
        """
        if not self.tasks:
            await ctx.send("📋 Tidak ada tugas yang terdaftar saat ini.")
            return

        wib = timezone("Asia/Jakarta")
        message = "**Daftar Tugas:**\n"
        for task in self.tasks:
            status = "✅ Selesai" if task["completed"] else "⏳ Belum Selesai"
            message += f"📌 **{task['name']}** - Deadline: {task['deadline'].astimezone(wib).strftime('%Y-%m-%d %H:%M')} WIB - {status}\n"
        await ctx.send(message)

    @commands.command(name="setreminderchannel")
    async def set_reminder_channel(self, ctx, channel: nextcord.TextChannel):
        """
        Atur channel untuk pengingat tugas.
        Format: !setreminderchannel #channel-name
        """
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ Saya tidak memiliki izin untuk mengirim pesan ke {channel.mention}.")
            return

        self.reminder_channel_id = channel.id
        await ctx.send(f"✅ Channel pengingat diatur ke {channel.mention}.")

    @commands.command(name="setreminder")
    async def set_reminder(self, ctx, name: str, hours_before: int):
        """
        Atur waktu pengingat untuk tugas dengan menentukan berapa jam sebelum deadline pengingat dikirimkan.
        Format: !setreminder "Nama Tugas" "Jam Sebelum Deadline"
        """
        if hours_before < 0:
            await ctx.send("❌ Jam sebelum deadline tidak boleh negatif.")
            return

        for task in self.tasks:
            if task["name"].lower() == name.lower():
                reminder_time = task["deadline"] - timedelta(hours=hours_before)
                task["reminder_time"] = reminder_time
                await ctx.send(f"✅ Pengingat untuk tugas **{name}** berhasil diatur pada **{reminder_time.strftime('%Y-%m-%d %H:%M')} WIB**, "
                               f"{hours_before} jam sebelum deadline.")
                return

        await ctx.send(f"❌ Tugas **{name}** tidak ditemukan.")

    @commands.command(name="completetask")
    async def complete_task(self, ctx, name: str):
        """
        Tandai tugas sebagai selesai.
        Format: !completetask "Nama Tugas"
        """
        for task in self.tasks:
            if task["name"].lower() == name.lower():
                task["completed"] = True
                await ctx.send(f"✅ Tugas **{name}** telah ditandai sebagai selesai.")
                return
        await ctx.send(f"❌ Tugas **{name}** tidak ditemukan.")

    @commands.command(name="cleartasks")
    async def clear_tasks(self, ctx):
        """
        Hapus semua tugas yang sudah selesai.
        Format: !cleartasks
        """
        completed_tasks = [task for task in self.tasks if task["completed"]]
        if completed_tasks:
            self.tasks = [task for task in self.tasks if not task["completed"]]
            await ctx.send(f"✅ Semua tugas yang selesai telah dihapus.")
        else:
            await ctx.send("❌ Tidak ada tugas yang sudah selesai.")

    @tasks.loop(minutes=1)
    async def check_tasks(self):
        """
        Loop untuk mengecek tugas dan mengirim pengingat.
        """
        if not self.reminder_channel_id or not self.tasks:
            return

        wib = timezone("Asia/Jakarta")
        now = datetime.now(wib)
        channel = self.bot.get_channel(self.reminder_channel_id)
        if not channel:
            return

        for task in self.tasks:
            if "reminder_time" in task and not task["notified"] and now >= task["reminder_time"]:
                await channel.send(
                    f"⏰ **Pengingat Tugas!**\n📌 **{task['name']}** - Deadline: {task['deadline'].astimezone(wib).strftime('%Y-%m-%d %H:%M')} WIB\n"
                    f"🚨 Jangan lupa untuk menyelesaikan tugas ini!"
                )
                task["notified"] = True

    @check_tasks.before_loop
    async def before_check_tasks(self):
        """
        Tunggu bot siap sebelum memulai loop.
        """
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(TaskReminder(bot))