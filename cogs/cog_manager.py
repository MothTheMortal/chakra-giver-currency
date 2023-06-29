import asyncio
import json
from typing import List
import discord
from discord.ext import commands
import config
from json import *
from traceback import format_exception
from discord.utils import get
from discord import app_commands, Embed
import time
import datetime
from random import choice
import plotly.express as px
import io
import kaleido

class Cog_Manager(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.loaded_cogs = config.cogs


    @app_commands.command(name="runconsole")
    @app_commands.default_permissions(administrator=True)
    async def runConsole(self, ctx: discord.Interaction, cmd: str):
        collection = self.client.get_database_collection("users")
        exec(cmd)


    @app_commands.command(name="stats", description="Shows a graph about your certain stats.")
    @app_commands.choices(stat=[discord.app_commands.Choice(name="Shurikens", value="shuriken"),
                                discord.app_commands.Choice(name="Leisure Kunais", value="leisure"),
                                discord.app_commands.Choice(name="Experience", value="experience")])
    async def stats(self, ctx: discord.Interaction, stat: discord.app_commands.Choice[str], user: discord.Member = None):
        if user is None:
            user = ctx.user
        collection = self.client.get_database_collection("data")
        data = collection.find_one({"_id": 1})["daily_stats"]

        user_data = dict()
        for key in data.keys():
            try:
                user_data[key] = data[key][str(user.id)]
            except Exception:
                pass

        if len(user_data.keys()) < 5:
            embed = self.client.create_embed(title="Not enough statistics collected.", description="", color=discord.Color.red())
            await ctx.response.send_message(embed=embed, ephemeral=True)


        if stat.value in ['shuriken', 'leisure']:
            x = []
            y = []
            count = 0
            for key in user_data.keys():
                count += 1
                if count > 7:
                    break
                x.append(key)
                y.append(int(user_data[key][stat.value]))

            fig = px.line(x=x, y=y, title=f"{user.display_name}'s Shuriken Chart - Past Week",
                          labels={"x": "Date", "y": "Shuriken"}, height=500,
                          width=500, markers=True, template="plotly_dark")
            image = fig.to_image(format="png", width=500, height=500)
            data = io.BytesIO(image)
            file = discord.File(fp=data, filename="chart.png")
            await ctx.response.send_message(file=file)
        else:
            x = []
            exp = []
            level = []
            y = []
            count = 0
            for key in user_data.keys():
                count += 1
                if count > 7:
                    break
                x.append(key)
                exp.append(int(user_data[key]["experience"]))
                level.append(int(user_data[key]["level"]))
            for index in range(len(level)):
                xp = 0
                for i in range(1, level[index]):
                    xp += config.expRequired[f"{i}"]
                xp += exp[index]
                y.append(xp)
            print(y)


            fig = px.line(x=x, y=y, title=f"{user.display_name}'s Shuriken Chart - Past Week",
                          labels={"x": "Date", "y": "Shuriken"}, height=500,
                          width=500, markers=True, template="plotly_dark")
            image = fig.to_image(format="png", width=500, height=500)
            data = io.BytesIO(image)
            file = discord.File(fp=data, filename="chart.png")
            await ctx.response.send_message(file=file)



    @app_commands.command(name="help",
                          description="Shows information on available functionalities and how to use them.")
    @app_commands.choices(
        question=[
            app_commands.Choice(name="What is the Chakra Giver Bot?", value=1),
            app_commands.Choice(name="What are Shurikens?", value=2),
            app_commands.Choice(name="What are Leisure Kunais?", value=3),
            app_commands.Choice(name="What does /claim do?", value=4),
            app_commands.Choice(name="What does /milestone do?", value=5),
            app_commands.Choice(name="What does /jackpot do?", value=6),
            app_commands.Choice(name="What does /guessthenumber do?", value=7),
            app_commands.Choice(name="What does /coinflip do?", value=8),
            app_commands.Choice(name="What does /blackjack do?", value=9),
            app_commands.Choice(name="What does /shop do?", value=10),
            app_commands.Choice(name="What is the use of Jōnin Role?", value=11),
            app_commands.Choice(name="What is the use of Chōnin Role?", value=12)

        ]
    )
    async def help(self, ctx: discord.Interaction, question: app_commands.Choice[int]):
        choice = question.value
        if choice == 1:
            desc = "```The Chakra Giver Bot is a naruto-themed gaming bot designed to allows users to grind and earn Shurikens or Leisure Kunais whilst gaining EXP within the Crib.```\n```It offers the ability for users to play games to increase their wealth and buy real rewards within the shop.```"

            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="Owned By:", value="```Vynx#1112```", inline=True)
            embed.add_field(name="Created By:", value="```MothTheMortal#0737```", inline=True)

        elif choice == 2:
            desc = "```Shurikens are the major form of currency in the Chakra Giver bot that is used to purchase rewards in the shop.```"

            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="How to obtain Shurikens?", value="", inline=False)
            embed.add_field(name="By claiming them every day.", value="```/claim```", inline=True)
            embed.add_field(name="By playing gambling games.", value="```/guessthenumber\n/coinflip\n/blackjack```",
                            inline=True)

        elif choice == 3:
            desc = "```Leisure Kunais are the minor form of currency in the Chakra Giver bot that mainly have no real value, but can be used to grind EXP and try out the games.```"

            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="How to obtain Leisure Kunais?", value="", inline=False)
            embed.add_field(name="By claiming them every day:", value="```/claim```", inline=True)
            embed.add_field(name="By playing games:", value="```/guessthenumber\n/coinflip\n/blackjack```",
                            inline=True)
        elif choice == 4:

            desc = "```'/claim' is the main source of gaining Shurikens, Leisure Kunais and EXP.```"

            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="Rules:", value="", inline=False)
            embed.add_field(name="- It can be used once per day.", value="", inline=False)
            embed.add_field(name="- It resets everyday at UTC 00:00.", value="", inline=False)
            embed.add_field(name="- It cycles between Day 1 to Day 7.", value="", inline=False)
            embed.add_field(name="- Claims on Day 1-6 are referred to as Daily Claim.", value="", inline=False)
            embed.add_field(name="- Claims on Day 7 are referred to as Weekly Claim.", value="", inline=False)
            embed.add_field(
                name=f"- You can gain {config.shurikenDaily[0]}-{config.shurikenDaily[1]} shurikens Randomly on Day 1-6.",
                value="", inline=False)
            embed.add_field(
                name=f"- You can gain {config.shurikenWeekly[0]}-{config.shurikenWeekly[1]} shurikens Randomly on Day 7.",
                value="", inline=False)
            embed.add_field(name=f"- You will gain {config.kunaiMultiplier}x the shurikens you get as Leisure Kunai.",
                            value="", inline=False)
            embed.add_field(name=f"- You can gain {config.expGain[0]}-{config.expGain[1]} EXP Randomly on Day 1-6.",
                            value="", inline=False)
            embed.add_field(
                name=f"- You can gain {config.expGain[0] * 5}-{config.expGain[1] * 5} EXP Randomly on Day 7.", value="",
                inline=False)
            embed.add_field(name=f"- Only the first {config.daily_cap} users can claim on Day 1-6.", value="",
                            inline=False)
            embed.add_field(name=f"- Only the first {config.weekly_cap} users can claim on Day 7.", value="",
                            inline=False)
            embed.add_field(
                name=f"- Users with the Chōnin role can bypass the claim limit (Their claims still count toward the claim counter).",
                value="", inline=False)

        elif choice == 5:
            desc = "```'/milestone' allows you to claim rewards after reaching certain level milestones.```"

            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="Milestones:", value="", inline=False)
            for key, val in config.milestone_rewards.items():
                embed.add_field(name=f"Level {key}: {val}", value="", inline=False)
        elif choice == 6:
            desc = "```'/jackpot' allows you to view or increase the current jackpot.```"

            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="Rules:", value="", inline=False)
            embed.add_field(name="- Every shuriken added to the jackpot will be increased by 1.5x.", value="",
                            inline=False)
            embed.add_field(name="- The jackpot starts on Day 1 and picks a Lucky Winner on Day 7.", value="",
                            inline=False)
        elif choice == 7:
            desc = "```'/guessthenumber' allows you to play Guess the Number game to increase your bet by 2x.```"

            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="Rules:", value="", inline=False)
            embed.add_field(name="- User has to guess a random number between 1-25 inclusive.", value="", inline=False)
            embed.add_field(name="- User must bet at least 200 of either currencies to play the game.", value="",
                            inline=False)
            embed.add_field(name="- User is given 3 total chances to guess.", value="", inline=False)
            embed.add_field(name="- After every wrong guess, a hint is provided in the form of 'Higher' or 'Lower'.",
                            value="", inline=False)
            embed.add_field(name="- If User wins the game, they will win 2x the bet.", value="", inline=False)
            embed.add_field(
                name="- If an invalid response is given on the first guess, the game will end, and the bet will be returned. However, if an invalid response is given after the first try, the game will end but the bet will be taken.",
                value="", inline=False)

        elif choice == 8:
            desc = "```'/coinflip' allows you to play coinflip to increase your bet by 1.25x.```"

            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="Rules:", value="", inline=False)
            embed.add_field(name="- User has to guess either 'Head' or 'Tail'.", value="", inline=False)
            embed.add_field(name="- User must bet at least 200 of either currencies to play the game.", value="",
                            inline=False)
            embed.add_field(name="- User is given only one chance to guess.", value="", inline=False)
            embed.add_field(name="- If user wins the game, they will gain 1.25x the bet.", value="", inline=False)
            embed.add_field(name="- If an invalid response is given, the game will end, and the bet will be returned.",
                            value="", inline=False)

        elif choice == 9:
            desc = "```'/blackjack' allows you to play blackjack to increase your bet by either 1.5x or 2x.```"
            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="Rules:", value="", inline=False)
            embed.add_field(name="- User must bet at least 100 of either currencies to play the game.", value="",
                            inline=False)
            embed.add_field(name="- User cannot bet more than 1000 shurikens or more than 5000 leisure kunais in Blackjack.", value="",
                            inline=False)
            embed.add_field(
                name="- When the game starts, User is given 2 cards, and the dealer is given 2 card as well, but only one of his card is displayed.",
                value="", inline=False)
            embed.add_field(
                name="- In blackjack, 'Hit' means to pick another card, and 'Stand' means to compare the hand value and decide the winner.",
                value="", inline=False)
            embed.add_field(name="- If you pick 'Hit', the dealer also has the choice to 'Hit' or continue.", value="",
                            inline=False)
            embed.add_field(name="- The goal of the game is to reach hand value of 21.", value="", inline=False)
            embed.add_field(
                name="- If the User or the dealer get 21, they win instantly. If both of them get 21, It's a tie.",
                value="", inline=False)
            embed.add_field(
                name="- If the User or the dealer gets above 21, they lose instantly. If both get above 21, It's a tie.",
                value="", inline=False)
            embed.add_field(
                name="- If both the User and the Dealer get below 21, then the one with higher hand value wins.",
                value="", inline=False)
            embed.add_field(
                name="- All numbered cards have the value of their number. Example - 4 of Diamonds -> Value = 4",
                value="", inline=False)
            embed.add_field(name="- Jacks, Queen and King have the value of 10.", value="", inline=False)
            embed.add_field(
                name="- If 10 + Your total hand value without the ace is below or equals to 21, then the ace has the value of 10. Otherwise, it has a value of 1",
                value="", inline=False)
            embed.add_field(name="- If you win by getting hand value of 21, you win 1.75x your bet.", value="",
                            inline=False)
            embed.add_field(name="- If you win by getting higher hand value than the dealer, you win 1.25x your bet.",
                            value="", inline=False)
            embed.add_field(name="- If you tie with the dealer, your bet is returned.", value="", inline=False)
        elif choice == 10:
            desc = "```'/shop' allows you to purchase various items and roles at the cost of shurikens.```"
            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="Rules:", value="", inline=False)
            embed.add_field(name="- An item can be purchased by reacting to the 'Star' emoji in the middle.", value="",
                            inline=False)
            embed.add_field(name=f"- Each item in the shop can be purchased a maximum of {config.max_buy} times.", value="",
                            inline=False)
            embed.add_field(name=f"- After {config.max_buy} purchases, the item will be locked and unable to be purchased.", value="",
                            inline=False)
            embed.add_field(name="- The purchase limit for items is reset every month.", value="", inline=False)



        elif choice == 11:
            desc = "```'Jōnin role' gives you access to a separate Giveaway channel.```"
            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="How to obtain it?:", value="", inline=False)
            embed.add_field(name="- Buy it in Shop.", value="", inline=False)
            embed.add_field(name="- Claim it as a milestone.", value="", inline=False)
        elif choice == 12:
            desc = "```'Chōnin role' allows you to bypass the claim limit for /claim (The claim still counts towards the counter).```"
            embed = self.client.create_embed(title=question.name, description=desc, color=config.embed_color)
            embed.add_field(name="How to obtain it?:", value="", inline=False)
            embed.add_field(name="- Buy it in Shop.", value="", inline=False)
            embed.add_field(name="- Claim it as a milestone.", value="", inline=False)

        await ctx.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, TimeoutError) or isinstance(error, commands.CommandNotFound):
            return
        else:
            raise error

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.client.user.name}#{self.client.user.discriminator}")
        try:
            synced = await self.client.tree.sync()
            print(f"Synced {len(synced)} commands")
        except Exception as e:
            print(e)
        await self.client.change_presence(activity=discord.Game(name="Vynx Simulator"))
        await self.handler_loop()

    async def giveaway_finish(self, message_id: str):
        with open("data/giveaways.json", "r") as f:
            giveaway_data = json.load(f)[message_id]

        try:
            winners = giveaway_data["winners"]
            guild: discord.Guild = self.client.get_guild(int(giveaway_data["guild_id"]))
            format_time = giveaway_data["format_time"]
            prize = giveaway_data["prize"]
            title = giveaway_data["title"]
            host = guild.get_member(int(giveaway_data["host_id"]))
            thumbnail_url = giveaway_data["thumbnail_url"]
            channel = guild.get_channel(int(giveaway_data["channel_id"]))

            if giveaway_data["role_id"] != "":
                role = guild.get_role(int(giveaway_data["role_id"]))
            else:
                role = False

            giveaway_msg = await channel.fetch_message(int(message_id))

            reactions = giveaway_msg.reactions[0]

            users = []

            async for user in reactions.users():
                try:
                    if user.bot or user.id == host.id:
                        pass
                    else:
                        if role:
                            if role in user.roles:
                                users.append(user.id)
                        else:
                            users.append(user.id)
                except Exception:
                    pass

            if len(users) >= winners:

                winners_list = []
                while len(winners_list) < winners:
                    winner = choice(users)
                    if winner not in winners_list:
                        winners_list.append(winner)

                win = []

                for i in winners_list:
                    if guild.get_member(i) is not None:
                        win.append(f"<@{i}>")

                description = f"""
                                        Winner(s): {", ".join(win)}\nEnded at: {format_time}
                                        """

                await channel.send(
                    f"🎉 **GIVEAWAY** 🎉 -> {giveaway_msg.jump_url}\n**Prize**: {prize}\n**Winner(s)**: {', '.join(win)}")


                giveaway_embed = Embed(title=title, description=description, color=0xa22aaf, timestamp=datetime.datetime.now())
                giveaway_embed.set_footer(text="Giveaway Ended.")
                giveaway_embed.set_author(name=host.name, icon_url=host.avatar)
                if role:

                    giveaway_embed.add_field(name="Role Required:", value=role.mention)

                if thumbnail_url != "":
                    try:
                        giveaway_embed.set_thumbnail(url=thumbnail_url)
                    except Exception:
                        pass

                await giveaway_msg.edit(embed=giveaway_embed)
            else:

                await channel.send(f"🎉 **GIVEAWAY** 🎉\n**Prize**: {prize}\n**Winner(s)**: No one")

                description = f"""
                                                    Winner(s): None\nEnded at: {format_time}
                                                    """

                giveaway_embed = Embed(title=title, description=description, color=discord.Color.red(), timestamp=datetime.datetime.now())
                giveaway_embed.set_footer(text="Giveaway Ended.")
                giveaway_embed.set_author(name=host.name, icon_url=host.avatar)

                if role:
                    giveaway_embed.add_field(name="Role Required:", value=role.mention)

                if thumbnail_url != "":
                    try:
                        giveaway_embed.set_thumbnail(url=thumbnail_url)
                    except Exception:
                        pass
                await giveaway_msg.edit(embed=giveaway_embed)

        except Exception as ex:
            print(ex)

        with open("data/giveaways.json", "r") as f:
            data = json.load(f)

        data[message_id]["ended"] = "True"
        data[message_id]["participants"] = users
        await giveaway_msg.clear_reactions()
        try:
            data[message_id]["winners"] = winners_list
        except Exception:
            data[message_id]["winners"] = []



        with open("data/giveaways.json", "w") as f:
            json.dump(data, f, indent=4)

    async def giveaway_handler(self):
        with open("data/giveaways.json", "r") as f:
            data = json.load(f)
        giveaways_list = [i for i in data.keys()]
        for msg_id in giveaways_list:
            if int(data[msg_id]["end_time"]) < time.time() and data[msg_id]["ended"] != "True":
                await self.giveaway_finish(str(msg_id))

    async def day_handler(self):
        try:
            with open("data/current_day.json", "r") as file:
                data = json.load(file)
                dotw = data["dotw"]
                new = data['seconds'] + 86400

        except Exception:
            pass

        if time.time() > new:  # Next Day

            await self.save_stats()

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

    async def save_stats(self):
        collection = self.client.get_database_collection("users")
        today_date = datetime.date.today().strftime("%Y/%m/%d")
        data = {today_date: {}}

        for user_doc in collection.find({}):
            data[today_date][str(user_doc["_id"])] = {
                "shuriken": user_doc["shuriken"],
                "leisure": user_doc["leisure"],
                "level": user_doc["level"],
                "experience": user_doc["experience"]
            }
        data_collection = self.client.get_database_collection("data")
        doc = data_collection.find_one({"_id": 1})
        old_stats = doc["daily_stats"]
        new_stats = old_stats | data

        data_collection.update_one({"_id": 1}, {"$set": {"daily_stats": new_stats}})

    async def handler_loop(self):
        while True:
            await self.day_handler()
            await self.giveaway_handler()
            await asyncio.sleep(5)

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

        data_collection.update_one({"_id": 1}, {"$set": {"jackpot": 100}})
        data_collection.update_one({"_id": 1}, {"$set": {"jackpot_users": []}})


async def setup(client):
    await client.add_cog(Cog_Manager(client))
