import nextcord
from nextcord.ext import commands, tasks
from datetime import datetime, timedelta

class ClassReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.class_schedule = {}
        self.reminder_time = 15
        self.sent_reminders = {}
        self.check_classes.start()

    def cog_unload(self):
        self.check_classes.cancel()

    @commands.command(name='setclass', help='Set a class schedule. Usage: !setclass <day> <time> <class_name>')
    async def set_class(self, ctx, day: str, time: str, class_name: str):
        if day not in self.class_schedule:
            self.class_schedule[day] = []

        class_time = datetime.strptime(time, '%H:%M').time()
        self.class_schedule[day].append({'time': class_time, 'name': class_name})
        await ctx.send(f"Class '{class_name}' set on {day} at {time}")

    @commands.command(name='schedule', help='Show the class schedule.')
    async def show_schedule(self, ctx):
        if not self.class_schedule:
            await ctx.send("No classes scheduled.")
            return

        schedule_message = "Class Schedule:\n"
        for day, classes in self.class_schedule.items():
            schedule_message += f"\n{day}:\n"
            for cls in classes:
                schedule_message += f"  {cls['time'].strftime('%H:%M')} - {cls['name']}\n"

        await ctx.send(schedule_message)

    @commands.command(name='removeclass', help='Remove a class schedule. Usage: !removeclass <day> <time>')
    async def remove_class(self, ctx, day: str, time: str):
        if day not in self.class_schedule:
            await ctx.send(f"No classes scheduled on {day}.")
            return

        class_time = datetime.strptime(time, '%H:%M').time()
        initial_count = len(self.class_schedule[day])
        self.class_schedule[day] = [cls for cls in self.class_schedule[day] if cls['time'] != class_time]

        if len(self.class_schedule[day]) < initial_count:
            await ctx.send(f"Class at {time} on {day} removed.")
            if not self.class_schedule[day]:
                del self.class_schedule[day]
        else:
            await ctx.send(f"No class found at {time} on {day}.")

    @tasks.loop(minutes=1)
    async def check_classes(self):
        now = datetime.now()
        current_time = now.time()
        current_day = now.strftime('%A')

        if current_day in self.class_schedule:
            for cls in self.class_schedule[current_day]:
                class_time = cls['time']
                reminder_time = (datetime.combine(now.date(), class_time) - timedelta(minutes=self.reminder_time)).time()

                class_key = f"{current_day}_{class_time.strftime('%H:%M')}_{cls['name']}"

                if reminder_time <= current_time < (datetime.combine(now.date(), class_time) + timedelta(minutes=1)).time():
                    if class_key not in self.sent_reminders:
                        channel = nextcord.utils.get(self.bot.get_all_channels(), name='general')
                        if channel:
                            await channel.send(f"Reminder: Class '{cls['name']}' starts in {self.reminder_time} minutes!")
                        self.sent_reminders[class_key] = True
                elif current_time > (datetime.combine(now.date(), class_time) + timedelta(minutes=1)).time():
                    if class_key in self.sent_reminders:
                        del self.sent_reminders[class_key]

def setup(bot):
    bot.add_cog(ClassReminder(bot))