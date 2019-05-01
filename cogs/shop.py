import discord
import json
from datetime import datetime
import random
import string

from discord.ext import commands

from bot import data


class Shop(commands.Cog, name='Shop', command_attrs=dict(hidden=False)):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.command(brief='Purchase an item from the shop.')
    async def buy(self, ctx, *, name):
        _name = name.title()
        try:
            item = self.data['shop']['items'][_name]
        except KeyError:
            await ctx.send(f'There are no items named `{_name}` in the shop! Here\'s what is available:')
            return await ctx.invoke(self.bot.get_command('shop'))

        user = self.data['users'][str(ctx.message.author.id)]

        if user['samcoins'] >= item['cost']:
            if item['stock'] > 0:
                if _name not in user['backpack']:
                    user['backpack'][_name] = {}
                    user['backpack'][_name]['date'] = datetime.now().strftime('%m/%d/%Y')
                    user['backpack'][_name]['desc'] = self.data['shop']['items'][_name]['desc']
                    user['samcoins'] -= item['cost']
                    self.data['sam']['samcoins'] += item['cost']
                    embed = discord.Embed(description=f'<:receipt:566402375687077891> You bought one `{_name}`.', color=0xC1CCE6)
                    embed.set_footer(text='The item has been placed in your backpack.')
                    if _name == 'Broadcast Code':
                        code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(6)])
                        user['backpack'][_name]['code'] = code
                        self.data['sam']['codes'][str(ctx.message.author.id)] = code
                    return await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(description=f'<:full:563308809817292800> You already have a(n) `{_name}` in your backpack!', color=0xC1CCE6)
                    return await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description=f'<:outofstock:563308809846521882> `{_name}` is out of stock.', color=0xC1CCE6)
                await ctx.send(embed=embed)
        else:
            return await ctx.send('You do not have enough money to buy that item.')
                

    @commands.command(brief='Display the Corridor Shop.')
    async def shop(self, ctx):
        embed = discord.Embed(title='**Corridor Shop**', color=0xC1CCE6)
        items = dict(self.data['shop']['items'])
        keys = list(items.keys())
        for key in keys:
            item = items[key]
            name = f'<:tag:563308809817161730> **{key.title()}**  <:samcoin:563447854308261890> {item["cost"]}'
            if item['stock'] > 0:
                name += f'    <:instock:563308809339011090> **In stock!**'
            else:
                name += '    <:outofstock:563308809846521882> **Out of stock.**'
            embed.add_field(name=name, value=f'**Description:** {item["desc"]}', inline=False)
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/562564068376969217/563310709753249815/shop.png')
        embed.set_footer(text='All proceeds are saved by Sam for gambling features (and cat treats).')
        
        await ctx.send(embed=embed)

    @commands.command(brief='Donate to the Corridor Shop.')
    async def donate(self, ctx, amount: int):
        self.data['users'][str(ctx.message.author.id)]['samcoins']
        if self.data['users'][str(ctx.message.author.id)]['samcoins'] >= amount:
            self.data['sam']['samcoins'] += amount
            self.data['users'][str(ctx.message.author.id)]['samcoins'] -= amount

        embed = discord.Embed(description=f'<:piggybank:563418186544971796> You donated {amount} SamCoin to the Corridor Shop. Thank you!', color=0xC1CCE6)

        await ctx.send(embed=embed)

    @commands.command(brief='Gift an item from your backpack to another employee.')
    async def gift(self, ctx, gift: str, user: discord.Member):
        gift = gift.title()
        item = dict(self.data['shop']['items'][gift])
        gifter = self.data['users'][str(ctx.message.author.id)]
        giftee = self.data['users'][str(user.id)]

        if gift not in gifter['backpack']:
            return await ctx.send(f'You do not have a(n) `{gift}` in your backpack.')

        g = gifter['backpack'].get(gift)

        if gift not in giftee['backpack']:
            giftee['backpack'][gift] = g
            gifter['backpack'].pop(gift)
            if gift == 'Broadcast Code':
                code = g['code']
                self.data['sam']['codes'].pop(str(ctx.message.author.id))
                self.data['sam']['codes'][str(user.id)] = code
            await ctx.send(f'You gifted {user.mention} one `{gift}`!')
        else:
            return await ctx.send(f'{user.name} already has one of that item in their backpack.')

        

    @commands.command(hidden=True)
    @commands.is_owner()
    async def give(self, ctx, amount: int):
        self.data['users'][str(ctx.message.author.id)]['samcoins'] += amount


def setup(bot):
    bot.add_cog(Shop(bot, data))
