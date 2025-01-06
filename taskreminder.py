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

    @commands.command(name="at")
    async def add_task(self, ctx, name: str, deadline: str):
        """
        Add a new task
        Format: y!at "Task Name" "YYYY-MM-DD HH:MM" (Zona WIB)
        """
        try:
            if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$", deadline):
                await ctx.send("❌ Incorrect date format. Use the format YYYY-MM-DD HH:MM (Jakarta Time Zone).")
                return

            wib = timezone("Asia/Jakarta")
            parsed_time = datetime.strptime(deadline, "%Y-%m-%d %H:%M")
            deadline_datetime = wib.localize(parsed_time)

            self.tasks.append({"name": name, "deadline": deadline_datetime, "notified": False, "completed": False})
            await ctx.send(f"✅ Task **{name}** has been successfully added with the deadline **{deadline_datetime.strftime('%Y-%m-%d %H:%M')} WIB**.")
        except ValueError as e:
            await ctx.send(f"❌ An error occurred while parsing the date: {str(e)}")

    @commands.command(name="rmvt")
    async def remove_task(self, ctx, name: str):
        """
        Remove a task by name
        Format: y!rmvt "Task Name"
        """
        for task in self.tasks:
            if task["name"].lower() == name.lower():
                self.tasks.remove(task)
                await ctx.send(f"✅ Task **{name}** has ben successfully removed.")
                return
        await ctx.send(f"❌ Task **{name}** not found.")

    @commands.command(name="lt")
    async def list_tasks(self, ctx):
        """
        View the list of all registered tasks
        Format: y!lt
        """
        if not self.tasks:
            await ctx.send("📋 There are no tasks registered at the moment.")
            return

        wib = timezone("Asia/Jakarta")
        message = "** Task List:**\n"
        for task in self.tasks:
            status = "✅ Completed" if task["completed"] else "⏳ Not Completed"
            message += f"📌 **{task['name']}** - Deadline: {task['deadline'].astimezone(wib).strftime('%Y-%m-%d %H:%M')} WIB - {status}\n"
        await ctx.send(message)

    @commands.command(name="setrec")
    async def set_reminder_channel(self, ctx, channel: nextcord.TextChannel):
        """
        Set the channel for task reminders.
        Format: y!setrec #channel-name
        """
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(f"❌ I do not have permission to send messages to {channel.mention}.")
            return

        self.reminder_channel_id = channel.id
        await ctx.send(f"✅ Reminder channel set to {channel.mention}.")

    @commands.command(name="setre")
    async def set_reminder(self, ctx, name: str, hours_before: int):
        """
        Set the reminder time for a task by specifying how many hours before the deadline the reminder should be sent.
        Format: !setreminder "Task Name" "Hours Before Deadline"
        """
        if hours_before < 0:
            await ctx.send("❌ Hours before deadline cannot be negative.")
            return

        for task in self.tasks:
            if task["name"].lower() == name.lower():
                reminder_time = task["deadline"] - timedelta(hours=hours_before)
                task["reminder_time"] = reminder_time
                await ctx.send(f"✅ Reminder for task **{name}** successfully set for **{reminder_time.strftime('%Y-%m-%d %H:%M')} WIB**, "
                               f"{hours_before} hours before the deadline.")
                return

        await ctx.send(f"❌ Task **{name}** not found.")

    @commands.command(name="compt")
    async def complete_task(self, ctx, name: str):
        """
        Mark a task as complete.
        Format: !completetask "Task Name"
        """
        for task in self.tasks:
            if task["name"].lower() == name.lower():
                task["completed"] = True
                await ctx.send(f"✅ Task **{name}** has been marked as complete.")
                return
        await ctx.send(f"❌ Task **{name}** not found.")

    @commands.command(name="ct")
    async def clear_tasks(self, ctx):
        """
        Remove all completed tasks.
        Format: !cleartasks
        """
        completed_tasks = [task for task in self.tasks if task["completed"]]
        if completed_tasks:
            self.tasks = [task for task in self.tasks if not task["completed"]]
            await ctx.send(f"✅ All completed tasks have been removed.")
        else:
            await ctx.send("❌ No tasks have been completed.")

    @tasks.loop(minutes=1)
    async def check_tasks(self):
        """
        Loop to check tasks and send reminders.
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
                    f"⏰ **Task Reminder!**\n📌 **{task['name']}** - Deadline: {task['deadline'].astimezone(wib).strftime('%Y-%m-%d %H:%M')} WIB\n"
                    f"🚨 Don't forget to complete this task!"
                )
                task["notified"] = True

    @check_tasks.before_loop
    async def before_check_tasks(self):
        """
        Wait for the bot to be ready before starting the loop.
        """
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(TaskReminder(bot))