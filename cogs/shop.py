import discord
import json
import time 

from discord.ext import commands

from bot import data


class Shop(commands.Cog, name='shop', command_attrs=dict(hidden=False)):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.command(brief='Purchase an item from the shop.')
    async def buy(self, ctx, *, name):
        # return await ctx.send('This command is unavailable while Sam is under development.')
        _name = name.title()
        try:
            item = self.data['shop']['items'][_name]
        except KeyError:
            await ctx.send(f'There are no items named `{_name}` in the shop! Here\'s what is available:')
            return await ctx.invoke(self.bot.get_command('shop'))

        user = self.data['users'][str(ctx.message.author.id)]

        if user['money'] >= item['cost'] and item['stock'] > 0:
            if _name not in user['inventory'] or user['inventory'][_name]['quantity'] < item['umax']:
                try:
                    user['inventory'][_name]['quantity'] += 1
                except KeyError:
                    user['inventory'][_name] = {}
                    user['inventory'][_name]['quantity'] = 1
                    user['inventory'][_name]['timestamp'] = time.time()
                user['money'] -= item['cost']
                item['stock'] -= 1
                self.data['sam']['bank'] += item['cost']
                return await ctx.send(f'You bought one `{_name}`.')
            else:
                return await ctx.send('You can\'t carry anymore of that item.')
        else:
            return await ctx.send('You either do not have enough money to buy that item or it is out of stock.')
                

    @commands.command(brief='Display the Corridor Shop.')
    async def shop(self, ctx):
        embed = discord.Embed(title=':sparkles: **Corridor Shop** :sparkles:', color=0xC1CCE6)
        items = dict(self.data['shop']['items'])
        keys = list(items.keys())
        for key in keys:
            item = items[key]
            name = f'❖ **{key.title()}** (${item["cost"]})'
            if item['stock'] > 0:
                name += f'    :white_check_mark: **In stock!** [{item["stock"]}]'
            else:
                name += '    :x: **Out of stock :(**'
            embed.add_field(name=name, value=f'**Description:** {item["desc"]}', inline=False)
        embed.set_footer(text='All proceeds are saved by Sam for gambling features (and cat treats).')
        
        await ctx.send(embed=embed)

    @commands.command(brief='Display your balance.', aliases=['bal'])
    async def balance(self, ctx):
        balance = self.data['users'][str(ctx.message.author.id)]['money']
        embed = discord.Embed(description=f':dollar: **`${balance:.2f}`** :dollar:', color=0xC1CCE6)
        embed.set_footer(text=f'{ctx.message.author.name}\'s current savings.')
        await ctx.send(embed=embed)

    @commands.command(brief='Donate to the Corridor Shop.')
    async def donate(self, ctx, amount: int):
        self.data['users'][str(ctx.message.author.id)]['money']
        if self.data['users'][str(ctx.message.author.id)]['money'] >= amount:
            self.data['sam']['bank'] += amount
            self.data['users'][str(ctx.message.author.id)]['money'] -= amount

        await ctx.send(f'You donated ${amount} to the Corridor Shop. Thank you!')

    @commands.command(brief='Gift an item from your inventory to another employee.')
    async def gift(self, ctx, gift: str, user: discord.Member):
        gift = gift.title()
        item = dict(self.data['shop']['items'][gift])
        gifter = self.data['users'][str(ctx.message.author.id)]
        giftee = self.data['users'][str(user.id)]

        if gift not in gifter['inventory']:
            return await ctx.send(f'You do not have a(n) `{gift}` in your inventory.')
        else:
            if gifter['inventory'][gift]['quantity']-1 is 0:
                gifter['inventory'].pop(gift)
            else:
                gifter['inventory']['gift']['quantity'] -= 1

        if gift not in giftee['inventory'] or giftee['inventory'][gift]['quantity'] < item['umax']:
            try:
                giftee['inventory'][gift]['quantity'] += 1
            except KeyError:
                giftee['inventory'][gift] = {}
                giftee['inventory'][gift]['quantity'] = 1
                giftee['inventory'][gift]['timestamp'] = time.time()
                return await ctx.send(f'You gifted {user.mention} one `{gift}`!')
        else:
            return await ctx.send(f'{user.name} cannot carry anymore of that item.')

    @commands.command(hidden=True)
    @commands.is_owner()
    async def give(self, ctx, amount: int):
        self.data['users'][str(ctx.message.author.id)]['money'] += amount


def setup(bot):
    bot.add_cog(Shop(bot, data))
