# -*- coding: utf-8 -*-
import discord
import json
import random

from discord.ext import commands
from datetime import datetime, timedelta
from bot import data

class BreakRoom(commands.Cog, name='Break Room', command_attrs=dict(hidden=False)):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.command(brief='Get free money once a day.')
    async def daily(self, ctx, choice: int):
        return await ctx.send('This command is currently unavailable.')
        cooldown = self.data['users'][str(ctx.message.author.id)].get('daily', None)
        today = datetime.now().strftime('%m/%d/%Y')
        if cooldown is not None and today == cooldown:
            return await ctx.send('You\'ve already rolled today.')

        if choice == random.randint(1, 100):
            embed = discord.Embed(title='**JACKPOT!**', color=0xC1CCE6)
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/562564068376969217/563310543927115777/bank.png')
            embed.add_field(name='You won 20! Congratulations!', value='<:coin:563308808990883850>'*8, inline=True)
            payout = 100
        else:
            board = [random.randint(1, 100) for x in range(100)]

            payout = 0
            matches = 0
            output = ''
            for counter, number in enumerate(board, start = 1):
                if number == choice:
                    output += '<:coin:563308808990883850> '
                    payout += 5
                    matches += 1
                else:
                    output += '`'+str(number).zfill(2)+'`'+' '
                if counter % 10 == 0:
                        output += '\n'

            embed = discord.Embed(title=f'{ctx.message.author.display_name}\'s Daily Roll', color=0xC1CCE6)
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/562564068376969217/563310573832503297/coin.png')
            embed.add_field(name='Board', value=f'**{output}**', inline=True)
            embed.set_footer(text=f'You won ${payout} with {matches} matches.')

        await ctx.send(embed=embed)

        self.data['users'][str(ctx.message.author.id)]['wallet'] += payout
        self.data['users'][str(ctx.message.author.id)]['daily'] = today

    @commands.command(brief='Snipe the last deleted message in the server.')
    async def snipe(self, ctx):
        snipe = self.data['sam'].pop('snipe', None)
        if snipe is None: return await ctx.send('I fired, and I missed.')
        message = snipe['message']
        user = self.bot.get_user(int(snipe['author']))

        embed = discord.Embed(title='**SNIPED!**', color=0xC1CCE6)
        embed.add_field(name=f'Message:', value=f'"{snipe["message"]}"', inline=True)
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/562564068376969217/563310713205161985/snipe.png')
        embed.set_footer(text=f'Authored by {user.name}. Deleted on {snipe["date"]}.', icon_url=user.avatar_url)

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(BreakRoom(bot, data))