# -*- coding: utf-8 -*-
import discord
import json
import random
import aiohttp
import pytz
from googlesearch import search as gsearch
import asyncio

from discord.ext import commands
from geopy.geocoders import Nominatim
from datetime import datetime
from bot import data, USER_AGENT, assets
from PIL import Image
from io import BytesIO

# grab darksky api key
with open("./config/config.json") as f:
    config = json.load(f)

weather_key = config['darkskykey']


class Util(commands.Cog, name='Utility', command_attrs=dict(hidden=False)):
    def __init__(self, bot, data, weather_key):
        self.bot = bot
        self.data = data
        self.weather_key = weather_key

    @commands.command(brief='Check the weather.', aliases=['w'])
    async def weather(self, ctx, *, location=None):
        await ctx.channel.trigger_typing()
        if location is None:
            location = self.data['users'][str(ctx.message.author.id)].get('location', None)
            if location is None:
                return await ctx.send('You did not provide a location and you do not have one set. To set a location, do `.weatherset`.')

        if ',' not in location:
            return await ctx.send('Your location is incorrectly formatted.') 

        args = location.split(',')
        city = args[0].strip().title()
        area = args[1].strip().title()
        if len(area) == 2:
            area = area.upper()

        geolocator = Nominatim(user_agent=USER_AGENT)
        location = geolocator.geocode(city+' '+area)
        if location is None:
            return await ctx.send('The location you provided is invalid.')

        request = f'https://api.darksky.net/forecast/{self.weather_key}/{location.latitude},{location.longitude}'
        async with aiohttp.ClientSession() as cs:
            async with cs.get(request) as r:
                response = await r.json()

        conditions = dict() 
        conditions['Temp'] = f'{round(response["currently"].get("temperature"))}°F ({round((response["currently"].get("temperature")-32)*(5/9))}°C)'
        conditions['Feels'] = f'{round(response["currently"].get("apparentTemperature"))}°F ({round((response["currently"].get("apparentTemperature")-32)*(5/9))}°C)'
        conditions['High'] = f'{round(response["daily"]["data"][0].get("temperatureHigh"))}°F ({round((response["daily"]["data"][0].get("temperatureHigh")-32)*(5/9))}°C)'
        conditions['Low'] = f'{round(response["daily"]["data"][0].get("temperatureLow"))}°F ({round((response["daily"]["data"][0].get("temperatureLow")-32)*(5/9))}°C)'
        conditions['Humidity'] = f'{response["currently"].get("humidity")*100:.0f}%'
        try:
            bearing = int((response['currently'].get('windBearing')/22.5)+.5)
        except KeyError:
            conditions['Wind'] = f'{int(response["currently"].get("windSpeed"))}mph'
        else:
            directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
            conditions['Wind'] = f'{directions[(bearing % 16)]} @ {int(response["currently"].get("windSpeed"))}mph'

        chance = f'\n{response["hourly"]["data"][0].get("precipProbability")*100:.0f}% chance of rain.'
        time = int(datetime.fromtimestamp(response['currently'].get('time'), tz=pytz.timezone(response.get('timezone'))).strftime('%H'))
        summary = response['currently'].get('summary').capitalize().strip('.')+' conditons.'
        forecast = 'Forecast: '+response['hourly'].get('summary').capitalize()
        
        icon = response['currently'].get('icon')
        thumbnail = assets['weather'].get(icon, None)
        if thumbnail is None:
            if icon == 'cloudy':
                if time > 6 and time < 18:
                    thumbnail = assets['weather'].get('daycloudy', None)
                else:
                    thumbnail = assets['weather'].get('partly-cloudy-night', None)
            elif icon == 'fog':
                if time > 6 and time < 18:
                    thumbsnail = assets['weather'].get('dayfog', None)
                else:
                    thumbnail = assets['weather'].get('nightfog', None)
            elif 'rain' in icon:
                if time > 6 and time < 18:
                    thumbnail = assets['weather'].get('dayrain', None)
                else:
                    thumbnail = assets['weather'].get('nightrain', None)
            else:
                thumbnail = assets['weather'].get('bothstorm', None)

        embed = discord.Embed(title=f'Weather for {city}, {area}', color=0xC1CCE6)
        embed.set_thumbnail(url=thumbnail)
        string = ''
        for key, value in conditions.items():
            string += f'\n{key}: {value}'
        string += chance
        embed.add_field(name=summary, value=f'```{string}```', inline=False)
        embed.set_footer(text=forecast)

        await ctx.send(embed=embed)

    @commands.command(brief='Set your weather location.', aliases=['setw'])
    async def setweather(self, ctx, *, location=None):
        if location is None:
            return await ctx.send('You did not provide a location.')

        if ',' not in location:
            return await ctx.send('Your location is incorrectly formatted.')

        args = location.split(',')
        city = args[0].strip().title()
        area = args[1].strip().title()
        if len(area) == 2:
            area = area.upper()

        self.data['users'][str(ctx.message.author.id)]['location'] = f'{city}, {area}'

    @commands.command(brief='Search Google.', aliases=['g'])
    async def google(self, ctx, *, search: str):
        await ctx.channel.trigger_typing()
        for result in gsearch(search, num=1, pause=0.5,  stop=1):
            await ctx.send(result)

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

        await ctx.send(f'<:search:563308809745989633> `{search}`:')
        await ctx.send(f'http://www.youtube.com/watch?v={addr}')

    @commands.command(brief='Get the color of a hex code.')
    async def color(self, ctx, code: str=None):
        if code is None:
            code = f'#{random.randint(0, 0xFFFFFF):06x}'

        try:
            image = Image.new('RGB', (512, 512), code)
        except ValueError:
            return await ctx.send('Your hex code is invalid.')

        with BytesIO() as buffer:
            image.save(buffer, format='png')
            buffer.seek(0)
            channel = self.bot.get_channel(566332251042873370)
            message = await channel.send(file=discord.File(fp=buffer, filename='color.png'))

        embed = discord.Embed(title=f'Hex color {code}.', description=datetime.now().strftime('%m/%d/%Y'), color=0xC1CCE6)
        embed.set_author(name=f'{ctx.message.author.name}', icon_url=ctx.message.author.avatar_url)
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/562564068376969217/566338155444437002/color.png')
        embed.set_image(url=message.attachments[0].url)
        await ctx.send(embed=embed)
        await asyncio.sleep(2)
        await message.delete()


def setup(bot):
    bot.add_cog(Util(bot, data, weather_key))
