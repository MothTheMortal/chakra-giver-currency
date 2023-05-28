import asyncio
import copy

import discord
from discord.ext import commands
import config
from requests import get
import json
import time
from discord import app_commands, Embed
from datetime import datetime
from random import randint
from random import choice
from random import shuffle
from discord.ui import Button, View
import math


class Games(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def checkUser(self, ctx, user):
        user_collection = self.client.get_database_collection("users")
        user_profile = user_collection.find_one({"_id": user.id})

        if user_profile is None:
            em = self.client.create_embed("Unknown User",
                                          "Please do /start before using any of the Bot currency related commands.",
                                          config.embed_color, user.name, user.avatar.url)
            await ctx.response.send_message(embed=em)
            x = await ctx.original_response()
            await x.delete(delay=10)
            return True
        return False

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
                                                              config.embed_color, user.name, user.avatar.url)
            if oldLevel + 1 in config.milestone_rewards.keys():
                val = f"Level {oldLevel + 1}"
            else:
                val = None
            levelup.add_field(name="Milestone Achieved:", value=val)
            oldLevel = oldLevel + 1
            await channel.send(embed=levelup)

        collection.update_one({"_id": user.id}, {"$set": {"level": level}})
        collection.update_one({"_id": user.id}, {"$set": {"experience": exp}})

    @app_commands.command(name="blackjack", description="Play blackjack game!")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Shuriken", value="shuriken"),
        app_commands.Choice(name="Leisure Kunai", value="leisure"),
    ])
    @app_commands.describe(bet="The amount of money you want to bet (Minimum 100)",
                           currency="The currency you want to bet in", )
    async def blackjack(self, ctx: discord.Interaction, currency: app_commands.Choice[str], bet: int):
        global em
        if await self.checkUser(ctx, ctx.user):
            return

        if bet < 100:
            em = self.client.create_embed("Invalid Blackjack Bet",
                                          f"You must bet at least 100 {currency.name} to play Blackjack!",
                                          config.embed_color, ctx.user.name, ctx.user.avatar.url)

            await ctx.response.send_message(embed=em)
            x = await ctx.original_response()
            return await x.delete(delay=5)
        collection = self.client.get_database_collection("users")
        user_doc = collection.find_one({"_id": ctx.user.id})
        if user_doc[currency.value] < bet:
            em = self.client.create_embed(f"You do not have enough {currency.name}!",
                                          f"You do not have enough {currency.name} to play Blackjack!",
                                          config.embed_color, ctx.user.name, ctx.user.avatar.url)

            await ctx.response.send_message(embed=em)
            x = await ctx.original_response()
            return await x.delete(delay=5)

        currency = currency.value

        if currency == "shuriken":
            emoji = config.emojis["shuriken"]
            name = "Shuriken"
        else:
            name = "Leisure Kunai"
            emoji = config.emojis["leisure"]
        deck = copy.deepcopy(config.deck)
        shuffle(deck)
        dealer_hand = []
        player_hand = []
        for i in range(2):
            dealer_hand.append(deck.pop(0))
            player_hand.append(deck.pop(0))
        em = self.client.create_embed(f"Blackjack", f"You bet {bet} {emoji}", config.embed_color,
                                      ctx.user.name, ctx.user.avatar.url)

        def add_hand_fields(em):
            val = config.format_hand(player_hand)
            val = " AND ".join(val)
            em.add_field(name=f"Your Hand:", value=val, inline=False)
            em.add_field(name="", value=f"**Your Hand Value:** {config.calculate_hand_value(player_hand)}", inline=False)
            em.add_field(name="------------------", value="")
            em.add_field(name=f"Dealer Hand:", value=f"{config.format_hand(dealer_hand)[0]} AND ?", inline=False)
            em.add_field(name="", value=f"**Dealer Hand Value:** {config.single_card_calculation(dealer_hand[0])} + ?",
                         inline=False)
            return em

        def end_add_hand_fields(em):
            val = config.format_hand(player_hand)
            val = " AND ".join(val)
            val2 = config.format_hand(dealer_hand)
            val2 = " AND ".join(val2)
            em.add_field(name="------------------", value="", inline=False)
            em.add_field(name="Your Hand:", value=val, inline=False)
            em.add_field(name="", value=f"**Your Hand Value:** {config.calculate_hand_value(player_hand)}", inline=False)
            em.add_field(name="------------------", value="")
            em.add_field(name=f"Dealer Hand: ", value=val2, inline=False)
            em.add_field(name="", value=f"**Dealer Hand Value:** {config.calculate_hand_value(dealer_hand)}",
                         inline=False)

            return em

        async def tie():
            em = self.client.create_embed(f"Blackjack", f"The game is a tie!", config.embed_color,
                                          ctx.user.name, ctx.user.avatar.url)
            em = end_add_hand_fields(em)
            em.set_footer(text="It's a tie!")
            await ctx.edit_original_response(view=None)
            return await ctx.edit_original_response(embed=em)

        async def win():
            em = self.client.create_embed(f"Blackjack", f"You won the game!", config.embed_color,
                                          ctx.user.name, ctx.user.avatar.url)
            if config.calculate_hand_value(player_hand) == 21:
                modifier = 1.5
            else:
                modifier = 1
            em.add_field(name=f"Winning:", value=f"{bet * modifier} {emoji}", inline=True)
            em.add_field(name="New Balance:", value=f"{user_doc[currency] + bet * modifier} {emoji}", inline=True)
            em = end_add_hand_fields(em)
            em.set_footer(text="You won!")
            collection.update_one({"_id": ctx.user.id}, {"$inc": {currency: bet * modifier}})
            await ctx.edit_original_response(view=None)

            return await ctx.edit_original_response(embed=em)


        async def loss():
            em = self.client.create_embed(f"Blackjack", f"You lost the game!", config.embed_color,
                                          ctx.user.name, ctx.user.avatar.url)
            em.add_field(name=f"Lost: ", value=f"{bet} {emoji}", inline=True)
            em.add_field(name="New Balance:", value=f"{user_doc[currency] - bet} {emoji}", inline=True)
            em = end_add_hand_fields(em)
            em.set_footer(text="You lost!")
            await ctx.edit_original_response(view=None)
            collection.update_one({"_id": ctx.user.id}, {"$inc": {currency: -bet}})
            return await ctx.edit_original_response(embed=em)

        async def hit(ctx: discord.Interaction):
            await game('👊')
            try:
                await ctx.response.defer()
            except Exception:
                print("Random error")

        async def block(ctx: discord.Interaction):
            await game('🛑')
            try:
                await ctx.response.defer()
            except Exception:
                print("Random error")
        em = add_hand_fields(em)

        button_hit = Button(label="Hit", style=discord.ButtonStyle.green, emoji='👊')
        button_block = Button(label="Stand", style=discord.ButtonStyle.red, emoji='🛑')
        button_hit.callback = hit
        button_block.callback = block
        view = View()
        view.add_item(button_hit)
        view.add_item(button_block)
        em.set_footer(text=f"Your Turn")
        await ctx.response.send_message(embed=em, view=view)
        # msg = await ctx.original_response()
        player_hand_value = config.calculate_hand_value(player_hand)
        dealer_hand_value = config.calculate_hand_value(dealer_hand)

        if player_hand_value > 21 and dealer_hand_value > 21:
            return await tie()
        elif player_hand_value > 21:
            return await loss()
        elif dealer_hand_value > 21:
            return await win()
        elif player_hand_value == 21 and dealer_hand_value == 21:
            return await tie()
        elif player_hand_value == 21:
            return await win()
        elif dealer_hand_value == 21:
            return await loss()




        async def game(reply):
            global em
            player_hand_value = config.calculate_hand_value(player_hand)
            dealer_hand_value = config.calculate_hand_value(dealer_hand)

            if player_hand_value > 21 and dealer_hand_value > 21:
                return await tie()
            elif player_hand_value > 21:
                return await loss()
            elif dealer_hand_value > 21:
                return await win()
            elif player_hand_value == 21 and dealer_hand_value == 21:
                return await tie()
            elif player_hand_value == 21:
                return await win()
            elif dealer_hand_value == 21:
                return await loss()

            if reply == "👊":

                player_hand.append(deck.pop(0))
                em = self.client.create_embed(f"Blackjack - {ctx.user.name}", f"You bet {bet} {emoji}",
                                              config.embed_color, ctx.user.name, ctx.user.avatar.url)
                em = add_hand_fields(em)
                await ctx.edit_original_response(embed=em)

            elif reply == '🛑':

                player_hand_value = config.calculate_hand_value(player_hand)
                dealer_hand_value = config.calculate_hand_value(dealer_hand)

                if player_hand_value > 21 and dealer_hand_value > 21:
                    return await tie()
                elif player_hand_value > 21:
                    return await loss()
                elif dealer_hand_value > 21:
                    return await win()
                elif player_hand_value == 21 and dealer_hand_value == 21:
                    return await tie()
                elif player_hand_value == 21:
                    return await win()
                elif dealer_hand_value == 21:
                    return await loss()
                elif player_hand_value > dealer_hand_value:
                    return await win()
                elif player_hand_value < dealer_hand_value:
                    return await loss()
                else:
                    return await tie()

            em.set_footer(text=f"Dealer's Turn")
            await ctx.edit_original_response(embed=em)
            await asyncio.sleep(1)

            if config.calculate_hand_value(dealer_hand) < 17:
                dealer_hand.append(deck.pop(0))
                em = self.client.create_embed(f"Blackjack - {ctx.user.name}", f"You bet {bet} {emoji}",
                                              config.embed_color, ctx.user.name, ctx.user.avatar.url)
                em = add_hand_fields(em)
                await ctx.edit_original_response(embed=em)

            player_hand_value = config.calculate_hand_value(player_hand)
            dealer_hand_value = config.calculate_hand_value(dealer_hand)

            if player_hand_value > 21 and dealer_hand_value > 21:
                return await tie()
            elif player_hand_value > 21:
                return await loss()
            elif dealer_hand_value > 21:
                return await win()
            elif player_hand_value == 21 and dealer_hand_value == 21:
                return await tie()
            elif player_hand_value == 21:
                return await win()
            elif dealer_hand_value == 21:
                return await loss()

            em.set_footer(text=f"Your Turn")
            await ctx.edit_original_response(embed=em)

    @app_commands.command(name="guessthenumber", description="Guess The Number Game")
    @app_commands.describe(bet="How much you want to bet (Minimum 200).",
                           currency="Which currency to use to bet with. ")
    @app_commands.choices(currency=[
        app_commands.Choice(name="Shurikens", value="shuriken"),
        app_commands.Choice(name="Leisure Kunai", value="leisure")
    ])
    async def gtn(self, ctx: discord.Interaction, currency: app_commands.Choice[str], bet: int):

        if await self.checkUser(ctx, ctx.user):
            return

        if bet < 200:
            em = self.client.create_embed("Invalid Guess the Number Bet",
                                          f"You must bet at least 200 {currency.name} to play Guess the Number",
                                          config.embed_color, ctx.user.name, ctx.user.avatar.url)
            await ctx.response.send_message(embed=em)
            x = await ctx.original_response()
            return await x.delete(delay=5)
        currency = currency.value

        if currency == "shuriken":
            emoji = config.emojis["shuriken"]
            name = "Shurikens"
            exp = randint(config.expGain[0], config.expGain[1])
        else:
            emoji = config.emojis['leisure']
            name = "Leisure Kunai"
            exp = int(randint(config.expGain[0], config.expGain[1]) / 10)

        collection = self.client.get_database_collection("users")
        user_doc = collection.find_one({"_id": ctx.user.id})
        modifier = 2

        if user_doc[currency] < bet:
            em = self.client.create_embed("Invalid Guess the Number Bet",
                                          f"You do not have enough {name} to bet.",
                                          config.embed_color, ctx.user.name, ctx.user.avatar.url)
            await ctx.response.send_message(embed=em)
            x = await ctx.original_response()
            return await x.delete(delay=5)

        em = self.client.create_embed(f"Guess the number!",
                                      f"{ctx.user.name} has bet {bet} {emoji}\nGuess the correct number between 1-25 to win {modifier}x your bet!\nYou are given 3 guesses.",
                                      config.embed_color, ctx.user.name, ctx.user.avatar.url)
        em.add_field(name="Bet:", value=f"{bet} {emoji}")
        em.add_field(name="Winning:", value=f"{modifier * bet} {emoji}")
        em.set_footer(text="Reply with your guess within 10 seconds.")
        random_num = randint(1, 25)
        print(ctx.user.name, "Guess number", random_num)

        await ctx.response.send_message(embed=em)

        collection.update_one({"_id": ctx.user.id}, {"$inc": {currency: -bet}})

        def check(msg):
            return msg.author == ctx.user and msg.channel == ctx.channel

        msg = await ctx.original_response()

        tries = config.gtn_tries
        guessed = False
        try:
            while tries > 0:
                response = await self.client.wait_for("message", check=check, timeout=10)
                guess = int(response.content)
                if guess == random_num:
                    guessed = True
                    em = self.client.create_embed(f"Guess the Number",
                                                  "You guessed the number correctly!", config.embed_color,
                                                  ctx.user.name, ctx.user.avatar.url)
                    em.add_field(name="Won:", value=f"{modifier * bet - bet} {emoji}", inline=True)
                    em.add_field(name="New Balance:",
                                 value=f"{int(user_doc[currency] + modifier * bet - bet)} {emoji}", inline=True)
                    em.add_field(name="EXP Gained:", value=f"{exp} EXP", inline=True)
                    collection.update_one({"_id": ctx.user.id}, {"$inc": {currency: bet * modifier}})
                    collection.update_one({"_id": ctx.user.id}, {"$inc": {"experience": exp}})
                    break

                else:
                    tries -= 1
                    if tries == 0:
                        break
                    if guess > random_num:
                        x = "Lower"
                    elif guess < random_num:
                        x = "Higher"
                    await msg.reply(f"Incorrect Guess. You have {tries} guesses left. Hint: {x}")

            if not guessed:
                em = self.client.create_embed(f"Guess the Number",
                                              f"You ran out of guesses!\nThe correct number was → {random_num}",
                                              config.embed_color, ctx.user.name, ctx.user.avatar.url)
                em.add_field(name="Lost:", value=f"{bet} {emoji}", inline=True)
                em.add_field(name="New Balance:", value=f"{int(user_doc[currency] - bet)} {emoji}",
                             inline=True)
                em.add_field(name="EXP Gained:", value=f"{exp} EXP", inline=True)
                collection.update_one({"_id": ctx.user.id}, {"$inc": {"experience": exp}})

            await msg.reply(embed=em)

        except Exception as ex:
            print(ex)
            if tries == 3:
                collection.update_one({"_id": ctx.user.id}, {"$inc": {currency: bet}})
            em = self.client.create_embed(f"Guess the Number", "Unknown Response",
                                          config.embed_color, ctx.user.name, ctx.user.avatar.url)
            await msg.edit(embed=em)
            await msg.delete(delay=5)

        await self.UpdateUserLevel(ctx.user, ctx.channel)

    @app_commands.command(name="add", description="Adds both currencies to a user.")
    @app_commands.default_permissions(administrator=True)
    async def add(self, ctx: discord.Interaction, value: int, user: discord.Member = None):
        if ctx.user.id not in config.gods:
            return
        try:
            if user is None:
                user2 = ctx.user
            else:
                user2 = user
            await self.client.database_user_preload(user2)
            collection = self.client.get_database_collection("users")
            c = ["shuriken", "leisure"]
            x = ""
            for currency in c:
                user_doc = collection.update_one({"_id": user2.id}, {"$inc": {currency: value}})
                x += f"{user2.mention}: {value} {config.emojis[currency]} added - Total balance -> {collection.find_one({'_id': user2.id})[currency]} {config.emojis[currency]}"
                x += "\n"
            await ctx.response.send_message(
                x,
                ephemeral=True)
        except Exception as er:
            print(er)
            c = await ctx.original_response()
            await c.reply("Error has error, try again")

    @app_commands.command(name="coinflip", description="Coin Flipping Game")
    @app_commands.describe(bet="How much you want to bet (Minimum 200).")
    @app_commands.choices(currency=[app_commands.Choice(name="Shurikens", value="shuriken"),
                                    app_commands.Choice(name="Leisure Kunai", value="leisure")])
    async def coinflip(self, ctx: discord.Interaction, currency: app_commands.Choice[str], bet: int):

        if await self.checkUser(ctx, ctx.user):
            return

        if bet < 200:
            em = self.client.create_embed("Invalid Coin Flip Bet",
                                          f"You must bet at least 200 {currency.name} to play Coin Flip",
                                          config.embed_color, ctx.user.name, ctx.user.avatar.url)
            await ctx.response.send_message(embed=em)
            x = await ctx.original_response()
            return await x.delete(delay=5)

        currency = currency.value
        if currency == "shuriken":
            emoji = config.emojis["shuriken"]
            name = "Shurikens"
            exp = randint(config.expGain[0], config.expGain[1])
        else:
            emoji = config.emojis['leisure']
            name = "Leisure Kunai"
            exp = int(randint(config.expGain[0], config.expGain[1]) / 10)

        modifier = 1.25
        collection = self.client.get_database_collection("users")
        user_doc = collection.find_one({"_id": ctx.user.id})

        if user_doc[currency] < bet:
            em = self.client.create_embed("Invalid Guess the Number Bet",
                                          f"You do not have enough {name} to bet.",
                                          config.embed_color, ctx.user.name, ctx.user.avatar.url)
            await ctx.response.send_message(embed=em)
            x = await ctx.original_response()
            return await x.delete(delay=5)

        choices = ["head", "tail"]
        picked = choice(choices)
        em = self.client.create_embed(f"Coin Flipping",
                                      f"{ctx.user.name} has bet {bet} {emoji}\n Guess either Head or Tail to win {modifier}x your bet",
                                      config.embed_color, ctx.user.name, ctx.user.avatar.url)
        em.add_field(name="Bet:", value=f"{bet} {emoji}")
        em.add_field(name="Winning:", value=f"{int(modifier * bet)} {emoji}")
        em.set_footer(text="Reply with your guess within 15 seconds.")
        await ctx.response.send_message(embed=em)
        collection.update_one({"_id": ctx.user.id}, {"$inc": {currency: -bet}})

        def check(msg):
            return msg.author == ctx.user and msg.channel == ctx.channel

        msg = await ctx.original_response()

        try:
            response = await self.client.wait_for("message", check=check, timeout=15)
            response = response.content.lower()
            if response == "tails":
                response = "tail"
            elif response == "heads":
                response = "head"

            if response == picked:
                em = self.client.create_embed(f"Coin Flipping", "You guessed correctly!",
                                              config.embed_color, ctx.user.name, ctx.user.avatar.url)
                em.add_field(name="Won:", value=f"{int(modifier * bet - bet)} {emoji}", inline=True)
                em.add_field(name="New Balance:",
                             value=f"{int(user_doc[currency] + int(modifier * bet - bet))} {emoji}",
                             inline=True)
                em.add_field(name="EXP Gained:", value=f"{exp} EXP", inline=True)
                collection.update_one({"_id": ctx.user.id}, {"$inc": {currency: bet * modifier}})
                collection.update_one({"_id": ctx.user.id}, {"$inc": {"experience": exp}})

            elif response in choices:
                em = self.client.create_embed(f"Coin Flipping",
                                              f"You guessed incorrectly!\nThe correct guess was {picked.title()}",
                                              config.embed_color, ctx.user.name, ctx.user.avatar.url)
                em.add_field(name="Lost:", value=f"{bet} {emoji}", inline=True)
                em.add_field(name="New Balance:",
                             value=f"{int(user_doc[currency] - bet)} {emoji}", inline=True)
                em.add_field(name="EXP Gained:", value=f"{exp} EXP", inline=True)
                collection.update_one({"_id": ctx.user.id}, {"$inc": {"experience": exp}})

            else:
                raise Exception

            await msg.edit(embed=em)
        except Exception as ex:
            collection.update_one({"_id": ctx.user.id}, {"$inc": {currency: bet}})
            em = self.client.create_embed(f"Coin Flipping", "Unknown Response", config.embed_color, ctx.user.name,
                                          ctx.user.avatar.url)
            await msg.edit(embed=em)
            await msg.delete(delay=5)

        await self.UpdateUserLevel(ctx.user, ctx.channel)


async def setup(client):
    await client.add_cog(Games(client))
