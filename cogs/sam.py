import discord
import aiohttp
import re
import asyncio
import time
from datetime import datetime, timedelta
from discord.ext import commands
import re
import random
import numpy as np

from bot import data, CATALOG_CHANNEL

class Sam(commands.Cog, name='Sam'):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.Cog.listener()
    async def on_ready(self):
        self.data['sam']['login'] = int(datetime.utcnow().timestamp())
        self.bot.owner = (await self.bot.application_info()).owner
        await self.bot.change_presence(activity=discord.Game("in the office | .help"))
        print('Online.')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return
        
        print(message.content)
        
        if message.channel.id == CATALOG_CHANNEL and (message.author != self.bot.user):
            await message.delete()
        elif not message.content.startswith(self.bot.command_prefix):
            # update the user's name
            self.data['users'][str(message.author.id)]['name'] = message.author.name
            # increase message counter
            self.data['users'][str(message.author.id)]['messages'] += 1
            # check if they've earned a samcoin
            if self.data['users'][str(message.author.id)]['messages'] % 5 == 0:
                self.data['users'][str(message.author.id)]['samcoins'] += 1
            # random chance to talk
            if random.randint(1, 10) == random.randint(1, 10):
                ctx = await self.bot.get_context(message)
                return await ctx.invoke(self.bot.get_command('talk'))
            # random chance to say meow when named
            if random.randint(1, 3) == random.randint(1, 3) and message.author is not self.bot.user:
                for word in message.content.split():
                    if word == 'sam':
                        await message.channel.send('meow')
                        break

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.content.startswith(self.bot.command_prefix) and (message.author is not self.bot.user):
            self.data['sam']['snipe'] = {"author": str(message.author.id), "message": message.content, "date": datetime.now().strftime('%m/%d/%Y')}

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = discord.utils.get(member.guild.roles, name='Employee')
        await member.add_roles(role)
        self.data['users'][str(member.id)] = {"member": member.name, "reprimands": 0, "samcoins": 0, "messages": 0, "inventory": {}, "office": {}}
        door = self.bot.get_channel(556682836388872192)
        info = self.bot.get_channel(556686992101081109)
        await door.send(f'Welcome to Quiet Corridor, {member.mention}! Please go to {info.mention} to get started.')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await asyncio.sleep(2)
        if member.name != self.data['sam'].get('banned', None):
            door = self.bot.get_channel(556682836388872192)
            await door.send(f'{member.mention} has left Quiet Corridor. :(')

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        self.data['sam']['banned'] = user.name
        self.data['users'].pop(str(user.id))
        door = self.bot.get_channel(556682836388872192)
        await door.send(f'{user.mention} has been fired (banned) from Quiet Corridor.')
        self.data['sam'].pop('banned')

    @commands.command(name='ping', brief="Check latency.")
    async def ping(self, ctx):
        embed = discord.Embed(description=f'<:timer:563309483313594369> Delay of ~{int(self.bot.latency*1000)}ms.', color=0xC1CCE6)
        await ctx.send(embed=embed)

    @commands.command(name='pet', brief='Give Sam pets.', aliases=['pat', 'love'])
    async def pet(self, ctx):
        self.data['sam']['pets'] += 1

        embed = discord.Embed(title='Sam says:', description=" ", color=0xC1CCE6)
        embed.add_field(name=f':sparkling_heart: :two_hearts: :sparkling_heart: :two_hearts:', value=f'I have been pet {self.data["sam"]["pets"]} times.', inline=False)
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/562564068376969217/563310697854009344/sam512.png')

        await ctx.send(embed=embed)

    @commands.command(brief='Get Sam\'s uptime.')
    async def uptime(self, ctx):
        delta = timedelta(seconds=int(datetime.utcnow().timestamp())) - timedelta(seconds=self.data['sam']['login'])
        embed = discord.Embed(description=f'<:on:563308809481617452> {delta.days} days, {delta.seconds//3600} hours, and {(delta.seconds//60)%60} minutes.', color=0xC1CCE6)
        await ctx.send(embed=embed)

    @commands.command(brief='View all the data Sam has on you.')
    async def userinfo(self, ctx):
        user = self.data['users'].get(str(ctx.message.author.id))
        embed = discord.Embed(title=f'{ctx.message.author.name}\'s data.', color=0xC1CCE6)
        for key, val in user.items():
            if isinstance(val, dict):
                continue
            else:
                name = key
                value = val
            embed.add_field(name=name, value=value, inline=True)
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/562564068376969217/563310723560636416/userinfo.png')
        embed.set_image(url=ctx.author.avatar_url)
        embed.set_footer(text='If you have any questions, please DM cursethrower#3089.')
        await ctx.send(embed=embed)

    @commands.command(brief='Make Sam talk to you.')
    async def talk(self, ctx):
        messages = []
        await ctx.channel.trigger_typing()
        try:
            async for message in ctx.channel.history(limit=150, oldest_first=False):
                if not message.content.startswith(self.bot.command_prefix) and (message.author != self.bot.user):
                    message = sanitize(message.content)
                    if len(message) > 0 and message != '.':
                        messages.append(message)
        except discord.errors.Forbidden:
            pass

        message = await do_markov(' '.join(messages).split())
        await ctx.send(message)


def sanitize(message):
        # remove links
        message = re.sub(r'https?:\/\/.*', '', message)
        # remove emojis and mentions
        message = re.sub(r'<.*>', '', message)
        # remove special characters
        message = re.sub('[^A-Za-z0-9 /\',.?\"-]+', '', message)
        # remove whitespace
        message = message.strip()

        if len(message) > 1 or message is not None:
            message = message.capitalize()
            if not message.endswith(".") and not message.endswith("?"):
                message += "."
            return message

def make_pairs(history):
    for i in range(len(history)-1):
        yield (history[i], history[i+1])

async def build_dict(history):
    pairs = make_pairs(history)
    word_dict = {}
    for word_1, word_2 in pairs:
        if word_1 in word_dict.keys():
            word_dict[word_1].append(word_2)
        else:
            word_dict[word_1] = [word_2]

    return word_dict

async def build_sentence(matrix, history, max_words):
    while True:
        while True:
            chain = [np.random.choice(history)]
            if chain[0][0].isupper():# and "." not in chain[0] and "?" not in chain[0]:
                break

        for x in range(max_words):
            try:
                chain.append(np.random.choice(matrix[chain[-1]]))
            except KeyError as e:
                print(e)
                break

        if chain[len(chain)-1].endswith("."):
            break
    
    for index, word in enumerate(chain):
        if word == 'i':
            chain[index] = 'I'
        if '.' in word:
            try:
                chain[index+1].capitalize()
            except IndexError:
                pass

    sentence = " ". join(chain).lower()
    sentence = sentence[0:len(sentence)]
        
    return sentence

async def do_markov(messages):
    matrix = await build_dict(messages)
    return await build_sentence(matrix, messages, random.randint(2,5))

def setup(bot):
    bot.add_cog(Talk(bot))


def setup(bot):
    bot.add_cog(Sam(bot, data))
