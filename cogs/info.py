# -*- coding: utf-8 -*-
import discord
import json
import random

from discord.ext import commands
from datetime import datetime, timedelta
from bot import data

class Information(commands.Cog, name='Information', command_attrs=dict(hidden=False)):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

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

    @commands.command(name='ping', brief="Check latency.")
    async def ping(self, ctx):
        embed = discord.Embed(description=f'<:timer:563309483313594369> Delay of ~{int(self.bot.latency*1000)}ms.', color=0xC1CCE6)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Information(bot, data))