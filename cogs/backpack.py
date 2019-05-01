# -*- coding: utf-8 -*-
import discord
import json
import random

from discord.ext import commands
from bot import data


class Backpack(commands.Cog, name='Backpack', command_attrs=dict(hidden=False)):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.command(brief='Display what\'s in your backpack.')
    async def backpack(self, ctx):
        embed = discord.Embed(title='**Backpack**', color=0xC1CCE6)
        backpack = self.data['users'][str(ctx.message.author.id)].get('backpack', None)
        keys = list(backpack.keys())
        for key in keys:
            item = backpack[key]
            name = f'<:receipt:566402375687077891> **{key.title()}** (Purchased {item["date"]})'
            embed.add_field(name=name, value=f'**Description:** {item["desc"]}', inline=False)
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/562564068376969217/563310539409981461/backpack.png')
        embed.set_footer(text=f'{self.data["users"][str(ctx.message.author.id)]["samcoins"]}', icon_url='https://cdn.discordapp.com/attachments/562564068376969217/563459364799905848/samcoin.png')


        await ctx.send(embed=embed)

    @commands.command(brief='Change the color of your badge.')
    async def badge(self, ctx, color: str):
        badge = self.data['users'][str(ctx.message.author.id)]['backpack'].pop("Shiny Badge", None)

        if badge is None:
            return await ctx.send('You do not have a Shiny Badge. Purchase one from the Corridor Shop.')

        if color == 'random':
            color = random.randint(0, 0xFFFFFF)
        else:
            color = int(color, 16)

        if color < 0 or color > 0xFFFFFF:
            return await ctx.send('You gave an invalid color value. The value must be a 6-character value such as `a6b3f9` or `random` for a random color.')

        guild = ctx.message.guild
        name = self.data['users'][str(ctx.message.author.id)]['name']
        # check if the role exists
        role = discord.utils.get(guild.roles, name=name)
        if role is None:
            role = await guild.create_role(name=name)

        await role.edit(color=discord.Color(color), position=len(guild.roles)-2)
        await ctx.message.author.add_roles(role)

    @commands.command(brief='Set up a broadcast event.')
    async def broadcast(self, ctx, code: str, index: str):
        if index not in self.data['catalog']['items'].keys():
            return await ctx.send("Invalid catalog index.")

        if code not in self.data['sam']['codes'].values():
            return await ctx.send('Invalid Broadcast Code.')

        if self.data['sam']['codes'].get(str(ctx.message.author.id), None) != code:
            await ctx.send('This code does not belong to you. Thief...')

        backpack_item = self.data['users'][str(ctx.message.author.id)]['backpack'].pop("Broadcast Code")
        self.data['sam']['codes'].pop(str(ctx.message.author.id))
        
        item = self.data['catalog']['items'].get(index)
        if not all(x in item.keys() for x in ['artist', 'title', 'cover']):
            return await ctx.send('The item you picked has missing artist, title, or cover information. Please go to #catalog and update it with `.update`.')

        embed = discord.Embed(title=item.get('link'), url=item.get("link"), color=0xC1CCE6)
        embed.set_author(name=f'Broadcast Code: {code}', icon_url=ctx.message.author.avatar_url)
        embed.add_field(name=f'Item {index}', value=f'{item.get("artist")} – {item.get("title")}')
        embed.set_image(url=item.get("cover"))
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/562564068376969217/563310631298531329/intercom.png')
        embed.set_footer(text='Can you listen right now? React below.')

        await ctx.send(discord.utils.get(ctx.guild.roles, name='Broadcast').mention)
        broadcast = self.bot.get_channel(556688777700048907)
        message = await broadcast.send(embed=embed)
        await message.add_reaction('instock:563308809339011090')
        await message.add_reaction('outofstock:563308809846521882')
        await message.pin()

    @commands.command(brief='Get your Broadcast Code.')
    async def getcode(self, ctx):
        code = self.data['users'][str(ctx.message.author.id)]['backpack'].get('Broadcast Code', None)

        if code is None:
            return await ctx.send('You do not have a Broadcast Code.')

        embed = discord.Embed(description=f'<:intercom:563308809737601024> `{code["code"]}`', color=0xC1CCE6)
        embed.set_footer(text='Only you can use this code.')
        await ctx.send(embed=embed)

    @commands.command(brief='Check your SamCoin funds.')
    async def funds(self, ctx):
        coins = self.data['users'][str(ctx.message.author.id)]['samcoins']
        embed = discord.Embed(description=f'<:samcoin:563447854308261890> {coins}', color=0xC1CCE6)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Backpack(bot, data))