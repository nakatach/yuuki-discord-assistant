import nextcord
import json
from nextcord.ext import commands

# Function to load the to-do list from a JSON file
def load_todo_list():
    try:
        with open('todo_list.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Function to save the to-do list to a JSON file
def save_todo_list(todo_list):
    with open('todo_list.json', 'w') as file:
        json.dump(todo_list, file)

# Create a command group or individual commands
class ToDoList(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.todo_list = load_todo_list()

    @commands.command(name='addtask')
    async def add_task(self, ctx, *, task: str):
        self.todo_list.append(task)
        save_todo_list(self.todo_list)
        await ctx.send(f'Task "{task}" has been added to the to-do list.')

    @commands.command(name='viewtasks')
    async def view_tasks(self, ctx):
        if not self.todo_list:
            await ctx.send("The to-do list is empty.")
        else:
            tasks = '\n'.join(f"{idx+1}. {task}" for idx, task in enumerate(self.todo_list))
            await ctx.send(f"Task list:\n{tasks}")

    @commands.command(name='removetask')
    async def remove_task(self, ctx, task_number: int):
        if 0 < task_number <= len(self.todo_list):
            removed_task = self.todo_list.pop(task_number - 1)
            save_todo_list(self.todo_list)
            await ctx.send(f'Task "{removed_task}" has been removed from the to-do list.')
        else:
            await ctx.send(f'Task number {task_number} not found.')
    
    @commands.command(name='clear')
    async def clear(self, ctx):
        self.todo_list.clear()
        save_todo_list(self.todo_list)
        await ctx.send("All tasks has been removed from the list")

    @commands.command(name='completetask')
    async def complete_task(self, ctx, task_number: int):
        if 0 < task_number <= len(self.todo_list):
            completed_task = self.todo_list[task_number - 1]
            self.todo_list[task_number - 1] = f"{completed_task} (Completed)"
            save_todo_list(self.todo_list)
            await ctx.send(f'Task "{completed_task}" has been marked as completed.')
        else:
            await ctx.send(f'Task number {task_number} not found.')

# Setup function to add Cog to bot
def setup(bot):
    bot.add_cog(ToDoList(bot))
