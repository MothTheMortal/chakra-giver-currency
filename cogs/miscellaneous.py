import copy

import discord
from discord.ext import commands
from time import monotonic
import config
from requests import get
import json
import asyncio
import time
from discord import app_commands, Embed
from discord.ext import tasks
from datetime import datetime, timedelta, timezone
from random import choice, sample


class Miscellaneous(commands.Cog):
    def __init__(self, client):
        self.client = client


    @app_commands.command(name="resetmilestone", description="Reset's a user's claimable milestone.")
    @app_commands.default_permissions(administrator=True)
    async def resetMilestone(self, ctx: discord.Interaction, user: discord.Member):
        if ctx.user.id not in config.gods:
            return
        collection = self.client.get_database_collection("users")
        collection.update_one({"_id": user.id}, {"$set": {"milestones": []}})
        await ctx.response.send_message(f"Reset milestone for {user.name}")

    async def Reward(self, user, reward, milestone, ctx):
        Type = config.milestone_type[milestone]

        if Type == "shuriken":
            amount = int(reward.split(" ")[0])
            collection = self.client.get_database_collection("users")
            collection.update_one({"_id": user.id}, {"$inc": {"shuriken": amount}})

        elif Type == "role":
            role_name = reward.split(" ")[0]
            role_id = config.roles[role_name.lower()]
            role = ctx.guild.get_role(role_id)
            await user.add_roles(role)

        else:
            redeem_channel = ctx.guild.get_channel(config.channel_ids["redeem"])
            em = self.client.create_embed(
                f"Level {milestone} Reward",
                f"{user.name}({user.mention}) has claimed {reward} reward.",
                config.embed_color
            )
            em.set_footer(text="Delete This Once Completed!")
            await redeem_channel.send(embed=em)

    @app_commands.command(name="setexp", description="Sets a user's experience.")
    @app_commands.default_permissions(administrator=True)
    async def setexp(self, ctx: discord.Interaction, user: discord.Member, exp: int):
        if ctx.user.id not in config.gods:
            return
        collection = self.client.get_database_collection("users")
        collection.update_one({"_id": user.id}, {"$set": {"experience": exp}})
        await ctx.response.send_message(f"{user.name}'s experience has been set to {exp} EXP.")

    async def checkUser(self, ctx, user):
        user_collection = self.client.get_database_collection("users")
        user_profile = user_collection.find_one({"_id": user.id})

        if user_profile is None:
            em = self.client.create_embed("Unknown User",
                                          "Please do /start before using_ any of the Bot currency related commands.",
                                          config.embed_color)
            await ctx.response.send_message(embed=em)
            x = await ctx.original_response()
            await x.delete(delay=10)
            return True
        return False

    @app_commands.command(name="milestone", description="Used to claim your milestone rewards")
    async def milestone(self, ctx: discord.Interaction):
        user = ctx.user

        if await self.checkUser(ctx, user):
            return

        collection = self.client.get_database_collection("users")
        user_doc = collection.find_one({"_id": user.id})
        user_claimed = user_doc["milestones"]
        rewards = config.milestone_rewards
        user_level = user_doc["level"]

        milestoneCheck = False
        milestones = []

        for key in config.milestone_rewards.keys():
            if user_level >= key:
                if key not in user_claimed:
                    milestoneCheck = True
                    milestones.append(key)
        if milestoneCheck:

            em = self.client.create_embed(
                f"{len(milestones)} Milestone(s) Claimed!",
                "",
                config.embed_color
            )
            for milestone in milestones:
                em.add_field(inline=True, name=f"Lvl {milestone} Milestone Reward:", value=rewards[milestone])
                collection.update_one({"_id": user.id}, {"$push": {"milestones": milestone}})

            await ctx.response.send_message(embed=em)

            for milestone in milestones:
                await self.Reward(user, rewards[milestone], milestone, ctx)
        else:
            em = self.client.create_embed(
                "No milestones to claim",
                "There are no milestones available to be claimed.",
                config.embed_color
            )
            await ctx.response.send_message(embed=em)

    async def UpdateUserLevel(self, user: discord.Member, channel):
        collection = self.client.get_database_collection("users")
        doc = collection.find_one({"_id": user.id})
        level = doc["level"]
        if level == 50:
            return
        exp = doc["experience"]
        level = doc["level"]
        expNext = config.expRequired[f"{level}"]
        count = 0
        while exp >= expNext:

            exp -= expNext
            count += 1
            level += 1
            if level > 50:
                level = 50
                break
            expNext = config.expRequired[f"{level}"]
        oldLevel = doc["level"]
        for i in range(1, count + 1):
            levelup: discord.Embed = self.client.create_embed(f"{user.name} has leveled up!",
                                                              f"Level {oldLevel} → Level {oldLevel + 1}",
                                                              config.embed_color)
            if oldLevel + 1 in config.milestone_rewards.keys():
                val = f"Level {oldLevel + 1}"
            else:
                val = None
            levelup.add_field(name="Milestone Achieved:", value=val)
            oldLevel = oldLevel + 1
            await channel.send(embed=levelup)

        collection.update_one({"_id": user.id}, {"$set": {"level": level}})
        collection.update_one({"_id": user.id}, {"$set": {"experience": exp}})

    @app_commands.command(name="level", description="Shows your Level and Experience.")
    async def level(self, ctx: discord.Interaction, user: discord.Member = None):
        global progress_bar
        if user is None:
            user = ctx.user

        if await self.checkUser(ctx, user):
            return
        em = self.client.create_embed(f"{user.name}'s Level", "Loading...", config.embed_color)
        await ctx.response.send_message(embed=em)
        msg = await ctx.original_response()

        collection = self.client.get_database_collection("users")
        user_data = collection.find_one({"_id": user.id})

        exp = user_data["experience"]
        level = user_data["level"]
        user_claimed_milestones = user_data["milestones"]
        next_level_exp = config.expRequired[f"{level}"]

        if level < 50:
            percentage = int(exp / next_level_exp * 100)

            total_progress = int(percentage / 10)
            if total_progress > 10:
                total_progress = 10
            progress_bar = [config.empty for _ in range(10)]
            for i in range(total_progress):
                progress_bar[i] = config.filled
            progress_bar = "".join(progress_bar)

        else:
            next_level_exp = config.expRequired[f"{level}"]
            if not next_level_exp == 0:
                percentage = int(exp / next_level_exp * 100)
            else:
                percentage = 100

        milestoneCheck = False
        milestones = []
        nextMilestone = None
        for key in config.milestone_rewards.keys():
            if level >= key:
                milestones.append(key)
                milestoneCheck = True
            if level < key:
                nextMilestone = key
                break

        if milestoneCheck is not False:
            for i in milestones.copy():
                if i in user_claimed_milestones:
                    milestones.remove(i)

        if not milestones:
            milestoneCheck = False
        title = f"{user.name}'s Level"
        if level < 50:
            desc = f"""
            **LEVEL**: {level}
            **EXP**: {exp}/{next_level_exp} ({percentage}%)
            
            **{level}** ➔ {progress_bar} ➔ **{level + 1}** 
            """
        else:
            desc = f"""
                        **LEVEL**: {level}
                        **EXP**: {exp}/{next_level_exp} ({percentage}%)

                         You have reached the max level **{level}**
                        """

        embed: discord.Embed = self.client.create_embed(title, desc, config.embed_color)
        if nextMilestone:
            embed.add_field(name="Next Milestone: ", inline=True, value=f"Level {nextMilestone}")
            embed.add_field(name="Next Milestone Reward: ", inline=True,
                            value=f"{config.milestone_rewards[nextMilestone]}")

        if milestoneCheck:
            milestones = list(map(str, milestones))
            embed.add_field(name="Claimable Milestones: ", inline=False,
                            value=f"Level {', Level '.join(milestones)}")
        embed.set_footer(text="Do /milestone to claim your rewards.")
        await msg.edit(embed=embed)

    # @app_commands.command(name="nextday", description="Changes the bot to the next day.")
    # @app_commands.default_permissions(administrator=True)
    # async def nextday(self, ctx: discord.Interaction):
    #     with open("data/current_day.json", "r") as file:
    #         data = json.load(file)
    #     new = data['seconds'] + 86400
    #     with open("data/current_day.json", "w") as file:
    #         data["seconds"] = new
    #         if data['dotw'] < 7:
    #             data['dotw'] += 1
    #         else:
    #             data['dotw'] = 1
    #         await ctx.response.send_message(f"Day {data['dotw']}, data resetting")
    #         json.dump(data, file, indent=4)
    #     collection = self.client.get_database_collection("data")
    #     collection.update_one({"_id": 1}, {"$set": {"daily_claims": []}})


    @app_commands.command(name="giveaway", description="Starts a giveaway.")
    @app_commands.describe(host="User who's hosting the giveaway", channel="Channel where the giveaway will be hosted.",
                           winners="Number of winners.", )
    @app_commands.default_permissions(administrator=True)
    async def giveaway(self, ctx: discord.Interaction, host: discord.Member, channel: discord.TextChannel, winners: int,
                       days: float, hours: float, minutes: float, prize: str, role: discord.Role = None,
                       thumbnail_url: str = ""):

        duration_secs = days * 86400 + hours * 3600 + minutes * 60
        delta_time = timedelta(days=days, hours=hours, minutes=minutes)
        unix_end_datetime = int((datetime.now() + delta_time).timestamp())

        format_time = f"<t:{unix_end_datetime}>"

        title = "🎉 " + prize + " 🎉"

        description = f"""
                Number of Winners: {winners}
                Ends: {format_time}
                """
        giveaway_embed = Embed(title=title, description=description, color=0xa22aaf, timestamp=datetime.now())
        giveaway_embed.set_footer(text="React to join giveaway.")
        giveaway_embed.set_author(name=host.name, icon_url=host.avatar)

        if role is not None:
            giveaway_embed.add_field(name="Role Required:", value=role.mention)

        if thumbnail_url is not None:
            try:
                giveaway_embed.set_thumbnail(url=thumbnail_url)
            except Exception:
                pass
        try:
            await ctx.response.send_message(f"Giveaway started for {prize}!", ephemeral=True)
        except:
            pass
        msg = await channel.send(embed=giveaway_embed)
        await msg.add_reaction("🎉")

        with open("data/giveaways.json", "r") as f:
            data = json.load(f)
        with open("data/giveaways.json", "w") as f:
            data[str(msg.id)] = {
                "guild_id": str(ctx.guild.id),
                "host_id": str(host.id),
                "winners": winners,
                "format_time": format_time,
                "prize": prize,
                "end_time": str(unix_end_datetime),
                "title": title,
                "thumbnail_url": thumbnail_url,
                "role_id": str(role.id) if role is not None else "",
                "channel_id": str(channel.id),
                "message_id": str(msg.id),
                "ended": "False"
            }
            json.dump(data, f, indent=4)

    @app_commands.command(name="reroll-giveaway", description="Rerolls a giveaway.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(message_id="Message ID of the giveaway to reroll.")
    async def reroll(self, ctx: discord.Interaction, message_id: str):

        with open("data/giveaways.json", "r") as file:
            data = json.load(file)

        if message_id not in data.keys():
            return await ctx.response.send_message("Giveaway not found!", ephemeral=True)

        giveaway_channel = ctx.guild.get_channel(int(data[message_id]["channel_id"]))
        giveaway_msg = await giveaway_channel.fetch_message(int(message_id))
        format_time = data[message_id]["format_time"]
        prize = data[message_id]["prize"]
        embed = giveaway_msg.embeds[0]


        winners = []

        for i in range(len(data[message_id]["winners"])):
            winner = f'<@{choice(data[message_id]["participants"])}>'
            while winner in winners:
                winner = f'<@{choice(data[message_id]["participants"])}>'
            winners.append(winner)

        await ctx.response.send_message(f"🎉 **GIVEAWAY RE-ROLLED** 🎉 -> {giveaway_msg.jump_url}\n**Prize**: {prize}\n**New Winner(s)**: {', '.join(winners)}")

        description = f"""
                                                Re-rolled Winner(s): {", ".join(winners)}\nEnded at: {format_time}
                                                """
        embed.description = description
        await giveaway_msg.edit(embed=embed)


    @app_commands.command(name="start", description="Start your journey on Chakra Giver!")
    async def start(self, ctx: discord.Interaction):
        genin = ctx.guild.get_role(config.roles["genin"])
        if await self.client.database_user_preload(ctx.user) == "Old":
            await ctx.response.send_message("User already exists!", ephemeral=True)
        else:
            await ctx.response.send_message("User created!", ephemeral=True)
        if genin not in ctx.user.roles:
            await ctx.user.add_roles(genin)

    @app_commands.command(name="lockitem", description="Locks an item in the shop.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        category="Shop Category",
        page="Page Number of the item."
    )
    @app_commands.choices(
        category=[
            app_commands.Choice(name="MLBB", value="mlbb"),
            app_commands.Choice(name="Discord", value="discord"),
            app_commands.Choice(name="Roles", value="roles"),
            app_commands.Choice(name="Roblox", value="roblox")
        ],
        lock=[
            app_commands.Choice(name="Lock Item", value="True"),
            app_commands.Choice(name="Unlock Item", value="False")
        ]
    )
    async def lockitem(self, ctx: discord.Interaction, category: app_commands.Choice[str], page: int,
                       lock: app_commands.Choice[str]):
        if ctx.user.id not in config.gods:
            return
        with open("data/items.json", "r") as file:
            data = json.load(file)
        data[category.value][page - 1]["lock"] = lock.value
        with open('data/items.json', "w") as file:
            json.dump(data, file, indent=4)
        await ctx.response.send_message(f"Shop Item has been edited!", ephemeral=True)

    @app_commands.command(name="slap", description="Slaps someone!")
    async def slap(self, ctx: discord.Interaction, user: discord.Member):

        URL = "https://api.otakugifs.xyz/gif?reaction=slap"
        response = get(URL)
        json_data = json.loads(response.text)
        gif_url = json_data["url"]
        if ctx.user == user:
            text = f'{ctx.user.name} LIKES SELF-HARM.'
        else:
            text = f'{ctx.user.name} BRUTALLY SLAPS {user.name}!'
        em: discord.Embed = self.client.create_embed("", "", config.embed_color, text, ctx.user.avatar.url)
        em.set_thumbnail(url=None)
        em.set_image(url=gif_url)
        await ctx.response.send_message(embed=em)

    @app_commands.command(name="punch", description="Punchs someone!")
    async def punch(self, ctx: discord.Interaction, user: discord.Member):
        URL = "https://api.otakugifs.xyz/gif?reaction=punch"
        response = get(URL)
        json_data = json.loads(response.text)
        gif_url = json_data["url"]
        if ctx.user == user:
            text = f'{ctx.user.name} LIKES SELF-HARM.'
        else:
            text = f'{ctx.user.name} PUNCHES {user.name}!'
        em: discord.Embed = self.client.create_embed("", "", config.embed_color, text, ctx.user.avatar.url)
        em.set_thumbnail(url=None)
        em.set_image(url=gif_url)
        await ctx.response.send_message(embed=em)

    @app_commands.command(name="hug", description="Hugs someone!")
    async def hug(self, ctx: discord.Interaction, user: discord.Member):
        URL = "https://api.otakugifs.xyz/gif?reaction=hug"
        response = get(URL)
        json_data = json.loads(response.text)
        gif_url = json_data["url"]
        if ctx.user == user:
            text = f'{ctx.user.name} NEEDS LOVE.'
        else:
            text = f'{ctx.user.name} HUGS {user.name}!'
        em: discord.Embed = self.client.create_embed("", "", config.embed_color, text, ctx.user.avatar.url)
        em.set_thumbnail(url=None)
        em.set_image(url=gif_url)
        await ctx.response.send_message(embed=em)

    @app_commands.command(name="tickle", description="Tickles someone!")
    async def tickle(self, ctx: discord.Interaction, user: discord.Member):
        URL = "https://api.otakugifs.xyz/gif?reaction=tickle"
        response = get(URL)
        json_data = json.loads(response.text)
        gif_url = json_data["url"]
        if ctx.user == user:
            text = f'{ctx.user.name} LIKES SELF-HARM.'
        else:
            text = f'{ctx.user.name} TICKLES {user.name}!'
        em: discord.Embed = self.client.create_embed("", "", config.embed_color, text, ctx.user.avatar.url)
        em.set_thumbnail(url=None)
        em.set_image(url=gif_url)
        await ctx.response.send_message(embed=em)

    @app_commands.command(name="lick", description="Licks someone!")
    async def lick(self, ctx: discord.Interaction, user: discord.Member):
        URL = "https://api.otakugifs.xyz/gif?reaction=lick"
        response = get(URL)
        json_data = json.loads(response.text)
        gif_url = json_data["url"]
        if ctx.user == user:
            text = f'{ctx.user.name} LIKES WETNESS.'
        else:
            text = f'{ctx.user.name} LICKS {user.name}!'
        em: discord.Embed = self.client.create_embed("", "", config.embed_color, text, ctx.user.avatar.url)
        em.set_thumbnail(url=None)
        em.set_image(url=gif_url)
        await ctx.response.send_message(embed=em)

async def setup(client):
    await client.add_cog(Miscellaneous(client))
