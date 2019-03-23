import discord
import aiohttp
import re

from discord.ext import commands

from bot import data


class Sam(commands.Cog, name='sam'):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.owner = (await self.bot.application_info()).owner
        await self.bot.change_presence(activity=discord.Game("in the office | .help"))
        print('online.')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user: return
        
        for word in message.content.split():
            if word == 'cat' or word == 'sam':
                await message.channel.send('meow')

        if not message.content.startswith(self.bot.command_prefix):
            self.data['users'][str(message.author.id)]['money'] += 0.50

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = discord.utils.get(member.guild.roles, name='employee')
        await member.add_roles(role)
        self.data['users'][str(member.id)] = {"member": member.name, "reprimands": 0, "money": 0, "inventory": {}, "office": {}}
        door = self.bot.get_channel(556682836388872192)
        info = self.bot.get_channel(556686992101081109)
        await door.send(f'Welcome to Quiet Corridor, {member.mention}! Please go to {info.mention} to get started.')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        self.data['users'].pop(str(member.id))
        door = self.bot.get_channel(556682836388872192)
        await door.send(f'{member.mention} has left Quiet Corridor. :(')

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        self.data['users'].pop(str(user.id))
        door = self.bot.get_channel(556682836388872192)
        await door.send(f'{user.mention} has been fired (banned) from Quiet Corridor.')

    @commands.command(name='ping', brief="Check latency.")
    async def ping(self, ctx):
        embed = discord.Embed(description=f':ping_pong: **Pong! Delay of ~{int(self.bot.latency*1000)}ms.**', color=0xC1CCE6)
        await ctx.send(embed=embed)

    @commands.command(name='pet', brief='Give Sam pets.', aliases=['pat', 'love'])
    async def pet(self, ctx):
        self.data['sam']['pets'] += 1

        embed = discord.Embed(title='Sam says:', description=" ", color=0xC1CCE6)
        embed.add_field(name=f':sparkling_heart: :two_hearts: :sparkling_heart: :two_hearts:', value=f'I have been pet {self.data["sam"]["pets"]} times.', inline=False)
        embed.set_thumbnail(url=self.bot.user.avatar_url)

        await ctx.send(embed=embed)

        if self.data['sam']['pets'] is 69:
            self.data['users'][str(ctx.message.author.id)]['money'] += 0.69
            await ctx.send('For obvious reasons, `$0.69` has been deposited to your account. ;)')
        elif self.data['sam']['pets'] is 420:
            self.data['users'][str(ctx.message.author.id)]['money'] += 4.20
            await ctx.send('For obvious reasons, `$4.20` has been deposited to your account. ;)')
        elif self.data['sam']['pets'] is 666:
            self.data['users'][str(ctx.message.author.id)]['money'] += 6.66
            await ctx.send('For obvious reasons, `$6.66` has been deposited to your account. ;)')

    @commands.command(brief='Search YouTube.')
    async def yt(self, ctx, *, search):
        request = 'https://www.youtube.com/results?search_query=' + search.replace(' ', '+')
        async with aiohttp.ClientSession() as cs:
            async with cs.get(request) as r:
                response = await r.text()

        try:
            addr = re.findall(r'href=\"\/watch\?v=(.{11})', response)[0]
        except IndexError:
            await ctx.send(f'Couldn\'t find a YouTube video for your search `{search}`.')
            return

        await ctx.send(f'First result for your search `{search}`:')
        await ctx.send(f'http://www.youtube.com/watch?v={addr}')

    @commands.command(brief='Change what Sam is listening to.')
    async def listen(self, ctx, *, string):
        await self.bot.change_presence(activity=discord.Activity(name=string, type=2))
        await ctx.send(f'Now listening to `{string}`.')

def setup(bot):
    bot.add_cog(Sam(bot, data))
