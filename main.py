import discord
from discord.ext import commands
import os
from database import init_db

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    await bot.tree.sync()
    print("Slash synced")

async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"cogs.{file[:-3]}")

init_db()

import asyncio
asyncio.run(load_cogs())

bot.run("YOUR_BOT_TOKEN")