import discord
import json
import asyncio

from discord.ext import commands
from bot import data

class Owner(commands.Cog, name='Owner', command_attrs=dict(hidden=True)):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.command(name='load', brief='Load a cog.')
    @commands.is_owner()
    async def load(self, ctx, cog: str):
        try:
            self.bot.load_extension('cogs.'+cog)
        except Exception as error:
            await ctx.send(f'Unable to load cog `{cog}`.')
            await ctx.send(f'Error: `{error}`')
        else:
            await ctx.send(f'Loaded cog `{cog}`.')

    @commands.command(name='unload', brief='Unloads a cog.')
    @commands.is_owner()
    async def unload(self, ctx, cog: str):
        try:
            self.bot.unload_extension('cogs.'+cog)
        except Exception as error:
            await ctx.send(f'Unable to unload cog `{cog}`.')
            await ctx.send(f'Error: `{error}`')
        else:
            await ctx.send(f'Unloaded cog `{cog}`.')

    @commands.command(name='reload', brief='Reload a cog.')
    @commands.is_owner()
    async def reload(self, ctx, cog: str):
        try:
            self.bot.unload_extension('cogs.'+cog)
            self.bot.load_extension('cogs.'+cog)
        except Exception as error:
            await ctx.send(f'Unable to reload cog `{cog}`.')
            await ctx.send(f'Error: `{error}`')
        else:
            await ctx.send(f'Reloaded cog `{cog}`.')

    @commands.command(name='logout', brief='Log Sam out.')
    @commands.is_owner()
    async def logout(self, ctx):
        with open('./config/data.json', 'w') as f:
            json.dump(self.data, f, indent=4)

        await self.bot.logout()

    @commands.command(name='hire', brief='Manually hire a member or members.')
    @commands.is_owner()
    async def hire(self, ctx, *args):
        if not args:
            members = ctx.message.guild.members
        else:
            members = [await commands.MemberConverter().convert(ctx, member) for member in list(args)]

        for member in members:
            role = discord.utils.get(member.guild.roles, name='Employee')
            await member.add_roles(role)
            self.data['users'][str(member.id)] = {"name": member.name, "reprimands": 0, "money": 0, "inventory": {}, "office": {}}

        await ctx.send(f'Sucessfully hired {", ".join([member.name for member in members])}.')

    @commands.command(name='payout', brief='Pay employees for their work while the bot was offline.')
    @commands.is_owner()
    async def payout(self, ctx):
        channels = ctx.message.guild.text_channels
        for channel in channels:
            async for message in ctx.message.channel.history(limit=1000):
                if not message.content.startswith(self.bot.command_prefix) and not message.author == self.bot.user:
                    try:
                        self.data['users'][str(message.author.id)]['money'] += 0.50
                    except KeyError:
                        pass

        await ctx.send('Payout complete.')

    @commands.command(brief='Export Sam\'s data to file.')
    @commands.is_owner()
    async def export(self, ctx):
        with open('./config/data.json', 'w') as f:
            json.dump(data, f, indent=4)

        await ctx.send('Exported data to file.')

    @commands.command(brief='Count each member\'s messages.')
    @commands.is_owner()
    async def count(self, ctx):
        # zero out the counters
        users = self.data['users']
        for key in users.keys():
            users[key]['messages'] = 0

        channels = ctx.guild.text_channels
        for channel in channels:
            await ctx.send(f'Counting messages in {channel.mention}.')
            async for message in channel.history(limit=None, reverse=False):
                    if not message.content.startswith(self.bot.command_prefix) and (message.author != self.bot.user):
                        try:
                            users[str(message.author.id)]['messages'] += 1
                        except KeyError:
                            pass

def setup(bot):
    bot.add_cog(Owner(bot, data))