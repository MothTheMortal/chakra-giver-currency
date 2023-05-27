import discord_module as discord
from discord.ext import commands
import json
import discord
import config
import asyncio
import time
import pymongo


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.database_client = pymongo.MongoClient(kwargs["mongodb_uri"])
        self.discord_database = self.database_client["bot2"]

    def insert_database_user(self, user: discord.Member):
        database_collection = self.get_database_collection("users")
        database_collection.insert_one({
            "_id": user.id,
            "shuriken": 0,
            "name": user.name,
            "experience": 0,
            "level": 1,
            "milestones": [],
            "leisure": 0
        })

    def get_database_collection(self, collection):
        return self.discord_database[collection]

    async def database_user_preload(self, user: discord.Member):
        database_count = self.get_database_collection("users").count_documents({"_id": user.id})

        if database_count > 1:
            print("Duplicate Documents", user.name, user.id)
        elif database_count == 1:
            return "Old"
        elif database_count == 0:
            self.insert_database_user(user)
            return "New"


    async def message_response(self, message, member, timeout):
        def check_message(to_check):
            if to_check.channel != message.channel:
                return False
            if to_check.author != member:
                return False

            return True

    async def message_reaction(self, message, member, timeout):
        def check_reaction(reaction, user):
            if reaction.message != message:
                return False
            if user != member:
                return False

            return True

        try:
            return str((await self.wait_for("reaction_add", check=check_reaction, timeout=timeout))[0].emoji)
        except asyncio.TimeoutError:
            return None

    @staticmethod
    def create_embed(title, description, color, name=None, icon=None) -> discord.Embed:
        if name is None:
            x = BotEmbed(title, description, color)
        else:
            x = BotEmbed(title, description, color, name, icon)

        return x

    async def setup_hook(self):
        for cog in config.cogs:
            await self.load_extension(f"cogs.{cog}")


class BotEmbed(discord.Embed):
    def __init__(self, title, description, color, name=None, icon=None):
        super().__init__(title=title, description=description, color=color)
        if name is None:
            self.set_author(name=config.name, icon_url=config.profile_picture)
        else:
            self.set_author(name=name, icon_url=icon)
        self.set_thumbnail(
            url=config.thumbnail)
