import discord
from client import Bot
from dotenv import load_dotenv
from os import getenv

if __name__ == "__main__":
    load_dotenv()

    client = Bot(command_prefix="?", intents=discord.Intents.all(), case_insensitive=True, help_command=None,
                 mongodb_uri=getenv("MONGODB_URI"))
    client.run(getenv("TEST_BOT_TOKEN"))
