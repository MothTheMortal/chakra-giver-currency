import asyncio
import json

import discord
from discord.ext import commands
import config
from json import *
from traceback import format_exception
from discord.utils import get
from discord import app_commands
import time
import datetime
from random import choice

class Cog_Manager(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.loaded_cogs = config.cogs

    # @app_commands.command(name="runconsole")
    # @app_commands.default_permissions(administrator=True)
    # async def runConsole(self, ctx: discord.Interaction, cmd: str):
    #     collection = self.client.get_database_collection("users")
    #     exec(cmd)

    # @app_commands.command(name="test")
    # @app_commands.default_permissions(administrator=True)
    # async def test(self, ctx: discord.Interaction):
    #     z = dict()
    #     for emoji in ctx.guild.emojis:
    #         emoji: discord.Emoji = emoji
    #         if emoji.name in config.emojis.keys():
    #             z[emoji.name] = f"<:{emoji.name}:{emoji.id}>"
    #     print(dumps(z, indent=4))
    #
    #
    #     await ctx.response.send_message("test")


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, TimeoutError) or isinstance(error, commands.CommandNotFound):
            return
        else:
            raise error

    @commands.Cog.listener()
    async def on_ready(self):
        print("Runnning update")
        print(f"Logged in as {self.client.user.name}#{self.client.user.discriminator}")
        try:
            synced = await self.client.tree.sync()
            print(f"Synced {len(synced)} commands")
        except Exception as e:
            print(e)
        await self.client.change_presence(activity=discord.Game(name="Vynx Simulator"))
        while True:
            await asyncio.sleep(1)
            try:
                with open("data/current_day.json", "r") as file:
                    data = json.load(file)
                    dotw = data["dotw"]
                    new = data['seconds'] + 86400
            except Exception:
                pass
            if time.time() > new:

                with open("data/current_day.json", "w") as file:
                    data["seconds"] = new
                    if data['dotw'] < 7:
                        data['dotw'] += 1
                    else:
                        data['dotw'] = 1

                    if data['dotw'] == 7:
                        await self.runJackpot()
                    if data['dotw'] == 1:
                        await self.startJackpot()

                    print(f"Day {dotw}, data resetting")
                    json.dump(data, file, indent=4)
                collection = self.client.get_database_collection("data")
                collection.update_one({"_id": 1}, {"$set": {"daily_claims": []}})

    async def startJackpot(self):
        em = self.client.create_embed(":moneybag: Jackpot :moneybag:", f"This week's jackpot has started!\nMake sure to participate in the jackpot!", config.embed_color)
        em.add_field(name="Ends on:", value=f"Day 7")
        em.set_footer(text="The jackpot has started!.")
        guild = self.client.get_guild(config.guild_id)
        channel = guild.get_channel(config.channel_ids["jackpot"])
        await channel.send(embed=em)

    async def runJackpot(self):

        data_collection = self.client.get_database_collection("data")
        collection = self.client.get_database_collection("users")
        data_doc = data_collection.find_one({"_id": 1})
        members = data_doc['jackpot_users']
        jackpot = data_doc['jackpot']
        emoji = config.emojis["shuriken"]
        guild = self.client.get_guild(config.guild_id)
        channel = guild.get_channel(config.channel_ids["jackpot"])

        if not members:
            em = self.client.create_embed(":moneybag: Jackpot :moneybag:", f"This week's jackpot has spun!\nNo winner was picked as no one participated ;(", config.embed_color)
        else:
            winner = choice(list(set(members)))
            em = self.client.create_embed(":moneybag: Jackpot :moneybag:", f"This week's jackpot has spun!\nA lucky winner has been chosen", config.embed_color)
            em.add_field(name="Lucky Winner:", value=f"<@{winner}>", inline=False)
            em.add_field(name="Jackpot Won: ", value=f"{jackpot} {emoji}", inline=False)
            em.set_footer(text="The jackpot as been reset.")
            collection.update_one({"_id": winner}, {"$inc": {"shuriken": jackpot}})

        await channel.send(embed=em)

        data_collection.update_one({"_id": 1}, {"$set": {"jackpot": 0}})
        data_collection.update_one({"_id": 1}, {"$set": {"jackpot_users": []}})


async def setup(client):
    await client.add_cog(Cog_Manager(client))
