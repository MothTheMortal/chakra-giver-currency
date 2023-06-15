import asyncio
import discord
from discord.ext import commands
import config
from requests import get
import json
import time
from discord import app_commands, Embed
from datetime import datetime
from random import randint
import math


class Currency(commands.Cog):
    def __init__(self, client):
        self.client = client

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

    async def resetShop(self):
        with open("data/items.json", "r") as file:
            data = json.load(file)

            for key in data.keys():
                for i in range(len(data[key])):
                    data[key][i]["lock"] = "False"
                    data[key][i]["locks"] = 0
        with open("data/items.json", "w") as file:
            json.dump(data, file, indent=4)

    async def monthlyResetShop(self):
        with open("data/current_month.txt", "r") as file:
            month = file.read()
        current_month = datetime.now().strftime("%B")
        if month != current_month:
            await self.resetShop()
            with open("data/current_month.txt", "w") as file:
                file.write(current_month)

    async def refreshShop(self):
        with open("data/items.json", "r") as file:
            data = json.load(file)

            for key in data.keys():
                for i in range(len(data[key])):
                    if data[key][i]["locks"] >= config.max_buy:
                        data[key][i]["lock"] = "True"
                        data[key][i]["locks"] = 0
        with open("data/items.json", "w") as file:
            json.dump(data, file, indent=4)

    async def checkUser(self, ctx, user):
        user_collection = self.client.get_database_collection("users")
        user_profile = user_collection.find_one({"_id": user.id})

        if user_profile is None:
            em = self.client.create_embed("Unknown User",
                                          "Please do /start before using any of the Bot currency related commands.",
                                          config.embed_color)
            await ctx.response.send_message(embed=em)
            x = await ctx.original_response()
            await x.delete(delay=10)
            return True
        return False

    async def verifyUser(self, ctx):
        test_embed: discord.Embed = self.client.create_embed("User Verification",
                                                             "Please react with the emoji below to run the command",
                                                             config.embed_color)
        test_embed.set_footer(text="You must react within 10 seconds.")
        await ctx.response.send_message(embed=test_embed)

        msg = await ctx.original_response()
        await msg.add_reaction("🔒")
        reply = await self.client.message_reaction(msg, ctx.user, 10)

        async def invalid_response():
            invalid_response_embed = self.client.create_embed(
                "Failed Verification",
                "No valid response was detected.",
                config.embed_color
            )

            await msg.edit(embed=invalid_response_embed)

        if reply == "🔒":
            response_embed = self.client.create_embed(
                "Verified Successfully",
                "Command will continue as is.",
                config.embed_color
            )
            await msg.edit(embed=response_embed)
            await msg.clear_reactions()
            return msg
        else:
            await invalid_response()
            await msg.clear_reactions()
            await msg.delete(delay=10)
            return None

    @app_commands.command(name="addtorole", description="Adds a currency to all users with the role.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(currency=[
        app_commands.Choice(name="Shurikens", value="shuriken"),
        app_commands.Choice(name="Leisure Kunai", value="leisure"),
        app_commands.Choice(name="Both", value="both")
    ])
    async def addtorole(self, ctx: discord.Interaction, currency: app_commands.Choice[str], role: discord.Role,
                        value: int):
        if ctx.user.id not in config.gods:
            return
        collection = self.client.get_database_collection("users")
        try:
            if currency.value == "shuriken":
                for user in role.members:
                    collection.update_many({"_id": user.id}, {"$inc": {"shuriken": value}})
            elif currency.value == "leisure":
                for user in role.members:
                    collection.update_many({"_id": user.id}, {"$inc": {"leisure": value}})
            else:
                for user in role.members:
                    collection.update_many({"_id": user.id}, {"$inc": {"leisure": value}})
                    collection.update_many({"_id": user.id}, {"$inc": {"shuriken": value}})

            await ctx.response.send_message(f"Done", ephemeral=True)
        except Exception:
            pass

    @app_commands.command(name="addall", description="Adds both currencies to all users who have Genin.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(currency=[
        app_commands.Choice(name="Shurikens", value="shuriken"),
        app_commands.Choice(name="Leisure Kunai", value="leisure"),
        app_commands.Choice(name="Both", value="both")
    ])
    async def add(self, ctx: discord.Interaction, currency: app_commands.Choice[str], value: int):
        if ctx.user.id not in config.gods:
            return
        collection = self.client.get_database_collection("users")
        if currency.value == "shuriken":
            collection.update_many({}, {"$inc": {"shuriken": value}})
        elif currency.value == "leisure":
            collection.update_many({}, {"$inc": {"leisure": value}})
        else:
            collection.update_many({}, {"$inc": {"shuriken": value}})
            collection.update_many({}, {"$inc": {"leisure": value}})

    @app_commands.command(name="leaderboard", description="Shows the leaderboard for a currency.")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Shurikens", value="shuriken"),
        app_commands.Choice(name="Leisure Kunai", value="leisure"),
        app_commands.Choice(name="Level", value="level"),
    ])
    async def lb(self, ctx: discord.Interaction, currency: app_commands.Choice[str], places: int = 10):
        currency = currency.value
        if currency == "level":
            tag = "highest leveled"
        else:
            emoji = config.emojis[currency]
            tag = "wealthiest"
        user_collection = self.client.get_database_collection("users")

        class LeaderBoardPosition:
            def __init__(self, id, coins, name, exp=None):
                self.id = id
                self.coins = coins
                self.name = name
                self.exp = exp

        leaderboard = []

        for user in user_collection.find():
            if not user["_id"] in config.gods:
                if currency == "level":
                    leaderboard.append(LeaderBoardPosition(user["_id"], int(user[currency]), user["name"], int(user["experience"])))
                else:
                    leaderboard.append(LeaderBoardPosition(user["_id"], int(user[currency]), user["name"]))


        top = sorted(leaderboard, key=lambda x: x.coins, reverse=True)
        if currency == "level":
            sorted_users = []
            current_level = None
            same_level_users = []

            for user in top:
                level = user.coins
                exp = user.exp

                if level != current_level:
                    sorted_users.extend(sorted(same_level_users, key=lambda x: x.exp, reverse=True))
                    same_level_users = []
                    current_level = level

                same_level_users.append(user)

            sorted_users.extend(sorted(same_level_users, key=lambda x: x.exp, reverse=True))
            top = sorted_users
        leaderboard_embed = self.client.create_embed(
            "Chakra Giver Leaderboard",
            f"The top {places} {tag} people in all of the Crib!",
            config.embed_color
        )

        for i in range(1, places + 1, 1):
            try:
                value_one = top[i - 1].id
                value_two = top[i - 1].coins
                value_three = top[i - 1].name
                if currency == "level":
                    exp = top[i - 1].exp
                    percentage = int(exp / config.expRequired[f"{value_two}"] * 100)

                    leaderboard_embed.add_field(
                        name=f"{i}. Level {value_two} ({percentage}%)",
                        value=f"<@{value_one}> - {value_three}",
                        inline=False
                    )
                else:
                    leaderboard_embed.add_field(
                        name=f"{i}. {value_two} {emoji}",
                        value=f"<@{value_one}> - {value_three}",
                        inline=False
                    )
            except IndexError:
                leaderboard_embed.add_field(name=f"**<< {i} >>**", value="N/A | NaN", inline=False)

        return await ctx.response.send_message(embed=leaderboard_embed)

    @app_commands.command(name="jackpot", description="Jackpot command.")
    @app_commands.choices(action=[
        app_commands.Choice(name="View Jackpot", value="view"),
        app_commands.Choice(name="Add to Jackpot", value="add"),
    ])
    @app_commands.describe(action="The action to execute.", value="The amount of money to add to the jackpot.")
    async def jackpot(self, ctx: discord.Interaction, action: app_commands.Choice[str], value: int = None):

        if await self.checkUser(ctx, ctx.user):
            return

        emoji = config.emojis["shuriken"]
        data_collection = self.client.get_database_collection("data")
        data_doc = data_collection.find_one({"_id": 1})
        jackpot = data_doc["jackpot"]

        with open("data/current_day.json", "r") as f:
            current_day = json.load(f)["dotw"]

        if current_day == 7:
            em = self.client.create_embed("Jackpot Inactive!", "Jackpot will start on Day 1.",
                                          config.embed_color)
            return await ctx.response.send_message(embed=em)

        if action.value == "add" and value is None:
            em = self.client.create_embed("No value provided!", "Please provide a value to add to the jackpot.",
                                          config.embed_color)
            return await ctx.response.send_message(embed=em)

        elif action.value == "add" and value is not None:
            collection = self.client.get_database_collection("users")
            user_doc = collection.find_one({"_id": ctx.user.id})

            if user_doc["shuriken"] < value:
                em = self.client.create_embed("Not enough shurikens!",
                                              "You do not have enough shurikens to add to the jackpot.",
                                              config.embed_color)
                return await ctx.response.send_message(embed=em)

            collection.update_one({"_id": ctx.user.id}, {"$inc": {"shuriken": -value}})

            data_collection.update_one({"_id": 1}, {"$inc": {"jackpot": int(value * 1.5)}})
            data_collection.update_one({"_id": 1}, {"$push": {"jackpot_users": ctx.user.id}})
            em = self.client.create_embed(f":moneybag: Jackpot Increased :moneybag: ",
                                          f"You added {value} {emoji} to the jackpot. All shurikens added to the jackpot will be x1.5",
                                          config.embed_color)
            value = int(value * 1.5)
            em.add_field(name="Previous Jackpot:", value=f"{jackpot} {emoji}")
            em.add_field(name="New Jackpot:", value=f"{jackpot + value} {emoji}")
            return await ctx.response.send_message(embed=em)


        else:
            with open("data/current_day.json", "r") as f:
                current_day = json.load(f)["dotw"]

            em = self.client.create_embed(":moneybag: Jackpot :moneybag:", "The Jackpot will end on **Day 7 **",
                                          config.embed_color)
            em.add_field(name="Jackpot:", value=f"{jackpot} {emoji}", inline=True)
            em.add_field(name="Current Day:", value=f"Day {current_day}", inline=True)
            em.add_field(name="Total Participants:", value=len(set(data_doc["jackpot_users"])), inline=True)
            return await ctx.response.send_message(embed=em)

    @app_commands.command(name="resetshoplock", description="Resets locks on all shop items.")
    @app_commands.default_permissions(administrator=True)
    async def resetShoplock(self, ctx: discord.Interaction):
        if ctx.user.id not in config.gods:
            return
        await self.resetShop()
        await ctx.response.send_message("All shops have been unlocked and set to 0 purchases", ephemeral=True)

    @app_commands.command(name="balance", description="Shows your balance.")
    async def balance(self, ctx: discord.Interaction, user: discord.Member = None):
        if user is None:
            user = ctx.user
        user_collection = self.client.get_database_collection("users")
        user_profile = user_collection.find_one({"_id": user.id})

        if await self.checkUser(ctx, user):
            return

        bal_embed: discord.Embed = self.client.create_embed(f"{user.name}'s Belt", "", config.embed_color, user.name,
                                                            user.avatar.url)
        bal_embed.add_field(name="Shurikens:", value=f"{int(user_profile['shuriken'])} {config.emojis['shuriken']}",
                            inline=True)
        bal_embed.add_field(name="Leisure Kunai:", value=f"{int(user_profile['leisure'])} {config.emojis['leisure']}",
                            inline=True)
        await ctx.response.send_message(embed=bal_embed)

    @app_commands.command(name="addcurrency", description="Adds shurikens to a user.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.choices(currency=[
        app_commands.Choice(name="Shurikens", value="shuriken"),
        app_commands.Choice(name="Leisure Kunai", value="leisure")
    ])
    async def addcurrency(self, ctx: discord.Interaction, currency: app_commands.Choice[str], value: int,
                          user: discord.Member = None):
        if ctx.user.id not in config.gods:
            return
        try:
            currency = currency.value
            if user is None:
                user2 = ctx.user
            else:
                user2 = user
            await self.client.database_user_preload(user2)
            collection = self.client.get_database_collection("users")
            user_doc = collection.update_one({"_id": user2.id}, {"$inc": {currency: value}})
            await ctx.response.send_message(
                f"{user2.mention}: {value} {config.emojis[currency]} added - Total balance -> {collection.find_one({'_id': user2.id})[currency]} {config.emojis[currency]}",
                ephemeral=True)
        except Exception as er:
            print(er)
            c = await ctx.original_response()
            await c.reply("Error has error, try again")

    @app_commands.command(name="shop", description="Allows you to purchase items.")
    @app_commands.choices(category=[
        app_commands.Choice(name="MLBB", value="mlbb"),
        app_commands.Choice(name="Discord", value="discord"),
        app_commands.Choice(name="Roles", value="roles"),
        app_commands.Choice(name="Roblox", value="roblox")
    ])
    async def shop(self, ctx: discord.Interaction, category: app_commands.Choice[str]):
        await self.monthlyResetShop()
        await self.refreshShop()
        category = category.value

        shuriken = config.emojis["shuriken"]

        with open("data/items.json", "r") as file:
            item_data = json.load(file)

        user_collection = self.client.get_database_collection("users")

        # if category is None:
        #     category_embed = self.client.create_embed(
        #         "Chakra Giver Shop Categories",
        #         "A list of every shop category that you can buy from!",
        #         config.embed_color
        #     )
        #     for shop_category in config.shop_categories:
        #         formal_category = config.formal_shop_categories[shop_category]
        #         category_embed.add_field(name=formal_category, value=f"`/shop {shop_category}`", inline=False)
        #
        #     category_embed.set_footer(text="No Refunds!")
        #     return await ctx.response.send_message(embed=category_embed)  # I
        #
        # category = category.lower()
        # if category not in config.shop_categories:
        #     category_embed = self.client.create_embed(
        #         "Invalid Shop Category",
        #         "There is no shop category by that name.",
        #         config.embed_color
        #     )
        #
        #     return await ctx.response.send_message(embed=category_embed)

        user_profile = user_collection.find_one({"_id": ctx.user.id})

        if user_profile is None:
            em = self.client.create_embed("Unknown User",
                                          "Please do /start before using any of the Bot currency related commands.",
                                          config.embed_color)
            await ctx.response.send_message(embed=em)
            x = await ctx.original_response()
            return await x.delete(delay=10)

        shop_embed = self.client.create_embed("Chakra Giver Shop", "Loading Shop Items...", config.embed_color)
        await ctx.response.send_message(embed=shop_embed)
        shop_message = await ctx.original_response()

        await shop_message.add_reaction("⬅")
        await shop_message.add_reaction("⭐")
        await shop_message.add_reaction("➡")

        shop_items = item_data[category]
        item_index = 0

        index_bounds = (0, len(shop_items) - 1)
        while True:

            shop_item = shop_items[item_index]
            item_type = shop_item["type"]

            if item_data[category][item_index]["lock"] == "True":
                lock_state = True
            else:
                lock_state = False

            item_embed: discord.Embed = self.client.create_embed("Chakra Giver Shop", shop_item["description"],
                                                                 config.embed_color)

            item_embed.add_field(
                name=shop_item["name"],
                value=f"Price: {shop_item['price']} {config.emojis['shuriken']}",
                inline=True
            )
            if lock_state:
                item_embed.set_footer(
                    text=f"This item has been locked - Page: {item_index + 1}/{index_bounds[1] + 1}")
            else:
                item_embed.set_footer(
                    text=f"Page: {item_index + 1}/{index_bounds[1] + 1} - Purchases: {shop_item['locks']}/{config.max_buy}")

            await shop_message.edit(embed=item_embed)
            shop_reply = await self.client.message_reaction(shop_message, ctx.user, 30)

            if shop_reply is None:
                return await shop_message.delete(delay=10)

            async def invalid_response():
                invalid_response_embed = self.client.create_embed(
                    "Invalid Response",
                    "The response that you provided to the question was not acceptable.",
                    config.embed_color
                )

                await shop_message.edit(embed=invalid_response_embed)

            if shop_reply not in ["⬅", "⭐", "➡"]:
                await invalid_response()
                return await shop_message.delete(delay=10)

            await shop_message.remove_reaction(shop_reply, ctx.user)

            if lock_state and shop_reply == "⭐":
                pass

            elif shop_reply == "⬅":
                item_index -= 1

                if item_index < index_bounds[0]:
                    item_index = index_bounds[1]

            elif shop_reply == "➡":
                item_index += 1

                if item_index > index_bounds[1]:
                    item_index = index_bounds[0]

            else:

                if item_type == "role":
                    role = ctx.guild.get_role(shop_item['role_id'])
                    if role in ctx.user.roles:
                        info_embed = self.client.create_embed(
                            "Invalid Item Purchase",
                            "You are unable to purchase this role as you already have it.", config.embed_color)
                        await shop_message.edit(embed=info_embed)
                        return await shop_message.delete(delay=10)

                if user_profile["shuriken"] < shop_item["price"]:
                    price_embed = self.client.create_embed(
                        "Invalid Item Purchase",
                        "You are unable to purchase this item as you lack sufficient funds.",
                        config.embed_color
                    )
                    await shop_message.edit(embed=price_embed)
                    return await shop_message.delete(delay=10)

                user_collection.update_one({"_id": ctx.user.id}, {"$inc": {"shuriken": -1 * shop_item["price"]}})

                if item_type == "transaction":
                    transaction_embed = self.client.create_embed(
                        "Transaction Made",
                        shop_item["transaction"].format(member=ctx.user),
                        config.embed_color
                    )

                    transaction_embed.add_field(
                        name="Shurikens Spent",
                        value=f"{shop_item['price']} {shuriken}",
                        inline=True
                    )

                    transaction_embed.add_field(
                        name="Staff Member Responsible",
                        value=f"<@!{shop_item['staff_id']}>",
                        inline=True
                    )

                    transaction_embed.set_footer(text="Delete This Once Completed!")

                    transaction_channel = self.client.get_channel(config.channel_ids["shop"])
                    await transaction_channel.send(embed=transaction_embed)

                    notification_message = await transaction_channel.send(f"<@!{shop_item['staff_id']}>")
                    await notification_message.delete()
                elif item_type == "role":
                    role = ctx.guild.get_role(shop_item['role_id'])
                    await ctx.user.add_roles(role)

                purchased_embed = self.client.create_embed(
                    "Item Purchased",
                    "Your item has been successfully purchased, please allow us time to process your transaction.",
                    config.embed_color
                )

                purchased_embed.add_field(name="Item Purchased", value=shop_item["name"], inline=True)

                purchased_embed.add_field(
                    name="Shurikens Spent",
                    value=f"{shop_item['price']} {shuriken}",
                    inline=True
                )
                with open("data/items.json", "r") as file:
                    data = json.load(file)
                data[category][item_index]["locks"] += 1

                with open("data/items.json", "w") as file:
                    json.dump(data, file, indent=4)

                await shop_message.edit(embed=purchased_embed)
                return await shop_message.delete(delay=10)

    @app_commands.command(name="claim",
                          description=f"Claim {config.shurikenDaily[0]}-{config.shurikenDaily[1]} shurikens every day and {config.shurikenWeekly[0]}-{config.shurikenWeekly[1]} every 7 days.")
    async def claim(self, ctx: discord.Interaction):
        msg = await self.verifyUser(ctx)
        if msg is None:
            return
        else:
            pass

        user_collection = self.client.get_database_collection("users")
        user_profile = user_collection.find_one({"_id": ctx.user.id})

        if user_profile is None:
            try:
                em = self.client.create_embed("Unknown User",
                                              "Please do /start before using any of the Bot currency related commands.",
                                              config.embed_color, ctx.user.name, ctx.user.avatar.url)
            except Exception:
                em = self.client.create_embed("Unknown User",
                                              "Please do /start before using any of the Bot currency related commands.",
                                              config.embed_color)
            await msg.edit(embed=em)
            x = await ctx.original_response()
            return await x.delete(delay=10)

        collection = self.client.get_database_collection("data")
        data = collection.find_one({"_id": 1})
        claims = data["daily_claims"]
        chounin = ctx.guild.get_role(config.roles["chounin"])
        with open("data/current_day.json", "r") as file:
            data = json.load(file)
            set_day = data['seconds'] + 86400

        if ctx.user.id in claims:
            try:
                error = self.client.create_embed("User has already claimed today.",
                                                 f"You have already claimed the daily.",
                                                 config.embed_color, ctx.user.name, ctx.user.avatar.url)
            except Exception:
                error = self.client.create_embed("User has already claimed today.",
                                                 f"You have already claimed the daily.",
                                                 config.embed_color)

            error.add_field(name="Time until next claim:", value=f"<t:{set_day}:R>", inline=True)

            return await msg.edit(embed=error)
        if data["dotw"] < 7:
            if len(claims) >= config.daily_cap and not chounin in ctx.user.roles:
                try:
                    em = self.client.create_embed("Daily Claim Limit has been reached.",
                                                  f"Today's daily claim limit has been reached. Please try again tomorrow.",
                                                  config.embed_color, ctx.user.name, ctx.user.avatar.url)
                except Exception:
                    em = self.client.create_embed("Daily Claim Limit has been reached.",
                                                  f"Today's daily claim limit has been reached. Please try again tomorrow.",
                                                  config.embed_color)

                em.add_field(name="Daily Claim Limit:", value=f"{len(claims)}/{config.daily_cap}", inline=True)
                em.add_field(name="Time until reset:", value=f"<t:{set_day}:R>", inline=True)
                return await msg.edit(embed=em)
            else:
                collection.update_one({"_id": 1}, {"$push": {"daily_claims": ctx.user.id}})

            shurikens = randint(config.shurikenDaily[0], config.shurikenDaily[1])
            exp = randint(config.expGain[0], config.expGain[1])
            userID = ctx.user.id
            collection = self.client.get_database_collection("users")
            kunai = shurikens * config.kunaiMultiplier
            collection.update_one({"_id": userID}, {"$inc": {"shuriken": shurikens}})
            collection.update_one({"_id": userID}, {"$inc": {"experience": exp}})
            collection.update_one({"_id": userID}, {"$inc": {"leisure": kunai}})
            emoji = config.emojis['shuriken']
            balance = collection.find_one({'_id': userID})['shuriken']

            try:
                em: discord.Embed = self.client.create_embed(f"@{ctx.user.name} - Daily - {shurikens} {emoji} Gained.",
                                                             f"",
                                                             config.embed_color, ctx.user.name, ctx.user.avatar.url)
            except Exception:
                m: discord.Embed = self.client.create_embed(f"@{ctx.user.name} - Daily - {shurikens} {emoji} Gained.",
                                                            f"",
                                                            config.embed_color)

            em.timestamp = datetime.now()
            em.add_field(name="Daily Claim Limit:", value=f"{len(claims) + 1}/{config.daily_cap}", inline=True)
            em.add_field(name="Time until Reset:", value=f"<t:{set_day}:R>", inline=True)
            em.add_field(name="New Balance:", value=f"{int(balance)} {emoji}", inline=True)
            em.add_field(name="EXP Gained:", value=f"{exp} EXP", inline=True)
            em.add_field(name="Leisure Kunai Gained:", value=f"{kunai} {config.emojis['leisure']}", inline=True)
            em.set_footer(text=f"Day {data['dotw']}")
            await msg.edit(embed=em)
        else:
            if len(claims) >= config.weekly_cap and chounin not in ctx.user.roles:
                try:
                    em = self.client.create_embed("Weekly Claim Limit has been reached.",
                                                  f"The weekly claim limit has been reached. Please try again tomorrow.",
                                                  config.embed_color, ctx.user.name, ctx.user.avatar.url)
                except Exception:
                    em = self.client.create_embed("Weekly Claim Limit has been reached.",
                                                  f"The weekly claim limit has been reached. Please try again tomorrow.",
                                                  config.embed_color)
                em.add_field(name="Weekly Claim Limit:", value=f"{len(claims)}/{config.weekly_cap}", inline=True)
                em.add_field(name="Time until reset:", value=f"<t:{set_day}:R>", inline=True)
                return await msg.edit(embed=em)
            else:
                collection.update_one({"_id": 1}, {"$push": {"daily_claims": ctx.user.id}})

            shurikens = randint(config.shurikenWeekly[0], config.shurikenWeekly[1])
            exp = randint(config.expGain[0], config.expGain[1]) * 5
            kunai = shurikens * config.kunaiMultiplier
            userID = ctx.user.id
            collection = self.client.get_database_collection("users")
            collection.update_one({"_id": userID}, {"$inc": {"shuriken": shurikens}})
            collection.update_one({"_id": userID}, {"$inc": {"experience": exp}})
            collection.update_one({"_id": userID}, {"$inc": {"leisure": kunai}})

            emoji = config.emojis['shuriken']
            balance = collection.find_one({'_id': userID})['shuriken']
            try:
                em: discord.Embed = self.client.create_embed(f"Weekly - {shurikens} {emoji} Gained.",
                                                             f"",
                                                             config.embed_color, ctx.user.name, ctx.user.avatar.url)
            except Exception:
                em: discord.Embed = self.client.create_embed(f"Weekly - {shurikens} {emoji} Gained.",
                                                             f"",
                                                             config.embed_color)

            em.timestamp = datetime.now()
            em.add_field(name="Weekly Claim Limit:", value=f"{len(claims) + 1}/{config.weekly_cap}", inline=True)
            em.add_field(name="Time until Reset:", value=f"<t:{set_day}:R>", inline=True)
            em.add_field(name="New Balance:", value=f"{int(balance)} {emoji}", inline=True)
            em.add_field(name="EXP Gained:", value=f"{exp} EXP", inline=True)
            em.add_field(name="Leisure Kunai Gained:", value=f"{kunai} {config.emojis['leisure']}", inline=True)

            em.set_footer(text=f"Day {data['dotw']}")
            await msg.edit(embed=em)
        await self.UpdateUserLevel(ctx.user, ctx.channel)


async def setup(client):
    await client.add_cog(Currency(client))
