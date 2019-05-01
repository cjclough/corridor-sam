# -*- coding: utf-8 -*-
import aiohttp
import asyncio
import discord
import json
import re

from discord.ext import commands
from bot import data
from io import BytesIO
from PIL import Image


''' HELPER FUNCTIONS '''

async def get_json(method, params):
    request = 'http://ws.audioscrobbler.com/2.0/?method='
    request += method
    for param in params:
        request += param
    request += '&format=json'

    async with aiohttp.ClientSession() as cs:
        async with cs.get(request) as r:
            return await r.json()

async def get_period(period):
    if period == 'weekly' or period == 'week' or period == 'w':
        return '7day'
    elif period == 'monthly' or period == 'month' or period == 'm':
        return '1month'
    elif period == 'yearly' or period == 'year' or period == 'y':
        return '12month'
    elif period == 'overall' or period == "all" or period == 'a':
        return 'overall'

async def get_limit(size):
    l, w = size.split('x')
    limit = int(l)*int(w)
    return str(limit)

''' END HELPER FUNCTIONS '''

# grab last.fm api key
with open("./config/config.json") as f:
    config = json.load(f)

api_key = config["lastfmkey"]


class Last(commands.Cog, name='last.fm'):
    def __init__(self, bot, api_key, data):
        self.bot = bot
        self.api_key = api_key
        self.data = data

    @commands.command(brief='Show your latest scrobble.')
    async def fm(self, ctx):
        try:
            user = self.data['users'][str(ctx.message.author.id)]['last.fm']
        except KeyError:
            return await ctx.send('You have not set your last.fm username. To do so, use `.fmset`.')

        tracks = await get_json('user.getrecenttracks', ['&api_key='+self.api_key, '&user='+user, '&limit=1'])
        track = tracks['recenttracks']['track'][0]

        embed = discord.Embed(description=" ", color=0xC1CCE6)
        embed.add_field(name=track['name'], value="\nfrom " + "*"+track['album']['#text']+"*"+"\nby "+track['artist']['#text'], inline=True)
        embed.set_author(name=str(ctx.message.author.display_name)+" on last.fm", url="https://www.last.fm/user/"+user, icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url=track['image'][2]['#text'])
        await ctx.send(embed=embed)

    @commands.command(brief='Generate a chart of your top albums. Defaults to weekly 3x3.')
    async def fmchart(self, ctx, period="weekly", size="3x3"):
        try:
            user = self.data['users'][str(ctx.message.author.id)]['last.fm']
        except KeyError:
            return await ctx.send('You have not set your last.fm username. To do so, use `.fmset`.')

        albums = await get_json('user.gettopalbums', ['&api_key='+self.api_key, '&user='+user, '&limit='+await get_limit(size), '&period='+await get_period(period)])
        covers = [album['image'][3]['#text'] for album in albums['topalbums']['album']]

        per_row = int(size[:size.find('x')])
        per_col = int(size[size.find('x')+1:])
        canvas = Image.new('RGB', (per_row*300, per_col*300))

        async with ctx.message.channel.typing():
            offset_x = 0
            offset_y = 0
            for cover in covers:
                if offset_x == canvas.width:
                    offset_x = 0
                    offset_y += 300
                try:
                    async with aiohttp.ClientSession() as cs:
                        async with cs.get(cover) as r:
                            response = await r.content.read()
                    image = Image.open(BytesIO(response))
                    canvas.paste(image, (offset_x, offset_y))
                except aiohttp.InvalidURL:
                    pass
                offset_x += 300

            with BytesIO() as buffer:
                image.save(buffer, format='png')
                buffer.seek(0)
                await ctx.send(file=discord.File(fp=buffer, filename='chart.png'))

            # make the embed
            embed = discord.Embed(description=" ", color=0xC1CCE6)
            embed.add_field(name=ctx.message.author.display_name+'\'s last.fm chart', value=period+', '+size, inline=True)
            embed.set_author(name=str(ctx.message.author.display_name)+' on last.fm', url='https://www.last.fm/user/'+user, icon_url=ctx.message.author.avatar_url)
            await ctx.send(embed=embed)

    @commands.command(brief='Set your last.fm username.')
    async def fmset(self, ctx, username=None):
        if username is None:
            await ctx.send('You did not provide a username.')
            return

        user = await get_json('user.getinfo', ['&api_key='+self.api_key, '&user='+username, '&limit=1'])

        if 'error' in user:
            await ctx.send('That user doesn\'t exist on last.fm. Did you make a typo?')
            return

        self.data['users'][str(ctx.message.author.id)]['last.fm'] = username

        await ctx.send(f'Set your last.fm username to `{username}`.')

    @commands.command(brief='Search YouTube for your latest scrobble.')
    async def fmyt(self, ctx):
        try:
            user = self.data['users'][str(ctx.message.author.id)]['last.fm']
        except KeyError:
            return await ctx.send('You have not set your last.fm username. To do so, use `.fmset`.')

        tracks = await get_json('user.getrecenttracks', ['&api_key='+self.api_key, '&user='+user, '&limit=1'])
        track = tracks['recenttracks']['track'][0]
        artist = track['artist']['#text']
        title = track['name']

        request = 'https://www.youtube.com/results?search_query=' + artist.replace(' ', '+') + title.replace(' ', '+')
        async with aiohttp.ClientSession() as cs:
            async with cs.get(request) as r:
                response = await r.text()

        try:
            addr = re.findall(r'href=\"\/watch\?v=(.{11})', response)[0]
        except IndexError:
            await ctx.send(f'Couldn\'t find a YouTube video for "{title}" by {artist}.')
            return

        await ctx.send(f'YouTube video for "{title}" by {artist}:')
        await ctx.send(f'http://www.youtube.com/watch?v={addr}')

def setup(bot):
    bot.add_cog(Last(bot, api_key, data))