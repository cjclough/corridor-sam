import discord
import time

from discord.ext import commands
from datetime import datetime

from bot import data, CATALOG_CHANNEL


class Catalog(commands.Cog, name='Catalog', command_attrs=dict(hidden=False)):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.command(brief='Add an item to the Quiet Catalog.')
    async def catalog(self, ctx, album: str):
        if ctx.message.channel.id != CATALOG_CHANNEL:
            return await ctx.send('You cannot use that command here.')

        if not album.startswith('https://'):
            await ctx.send('You did not provide a valid link.')

        self.data['catalog']['entries'] += 1
        index = str(self.data['catalog']['entries']).zfill(3)
        date = datetime.now().strftime('%m/%d/%Y')
        self.data['catalog']['items'][index] = {"index": index, "link": album, "archiver": ctx.message.author.id, "date": date, "ratings": {}}
        embed = await self.make_embed(self.data['catalog']['items'][index])
        channel = self.bot.get_channel(CATALOG_CHANNEL)
        message = await channel.send(embed=embed)
        self.data['catalog']['items'][index]['message'] = message.id

    @commands.command(brief='Rate an album in the Quiet Catalog.')
    async def rate(self, ctx, index: str, rating: int):
        if ctx.message.channel.id != CATALOG_CHANNEL:
            return await ctx.send('You cannot use that command here.')

        if index == "current":
            index = str(self.data['catalog']['entries']).zfill(3)

        if rating < 1 or rating > 10:
            return ctx.send('Your rating is invalid.')
        
        ratings = self.data['catalog']['items'][index]['ratings']
        ratings[str(ctx.message.author.id)] = rating
        avg = 0
        for rating in list(ratings.values()):
            avg += rating
        avg /= len(ratings)
        self.data['catalog']['items'][index]['average'] = avg

        embed = await self.make_embed(self.data['catalog']['items'][index])
        await self.bot.http.edit_message(self.data['catalog']['items'][index]['message'], CATALOG_CHANNEL, embed=embed.to_dict())
    
    @commands.command(brief='Search the Quiet Catalog by index.')
    async def index(self, ctx, index: str):
        if index == "current":
            index = str(self.data['catalog']['entries']).zfill(3)
        
        if index not in self.data['catalog']['items']:
            await ctx.send(f'Item {index} doesn\'t exist in the catalog.')
        
        item = dict(self.data['catalog']['items'][index])
        embed = await self.make_embed(item)
        await ctx.send(embed=embed)

    @commands.command(brief='Search the Quiet Catalog by datapoint.')
    async def search(self, ctx, search: str, *args):
        searches = set(['artist', 'title', 'year', 'genre', 'average'])
        if search not in searches:
            return await ctx.send(f'You gave an invalid search key. Valid keys are: `{searches}`')

        catalog = self.data['catalog'].get('items')

        matches = []
        for key, value in catalog.items():
            try:
                if search == 'average':
                    if value[search] >= int(args[0]) and value[search] <= int(args[1]):
                        matches.append(key)
                elif args[0].title() in value[search]:
                    matches.append(key)
            except KeyError:
                pass

        if not matches:
            return await ctx.send('No items found.')
        elif len(matches) == 1:
            await ctx.send('Found exactly one match:')
            await ctx.invoke(self.bot.get_command('index'), index=matches[0])
        else:
            await ctx.send(f'{str(len(matches))} matches found:\n`{", ".join(matches)}`')

    @commands.command(brief='Update an item in the Quiet Catalog.')
    async def update(self, ctx, index: str, field: str, *, data: str):
        if ctx.message.channel.id != CATALOG_CHANNEL:
            return await ctx.send('You cannot use that command here.')

        if field not in ['link', 'artist', 'title', 'year', 'genre', 'rym', 'cover', 'complete']:
            return await ctx.send(f'You gave an invalid field to update.')

        if index == "current":
            index = str(self.data['catalog']['entries']).zfill(3)

        self.data['catalog']['items'][index][field] = data
        if field in ['artist', 'title', 'genre']:
            self.data['catalog']['items'][index][field] = data.title()

        embed = await self.make_embed(self.data['catalog']['items'][index])
        await self.bot.http.edit_message(self.data['catalog']['items'][index]['message'], CATALOG_CHANNEL, embed=embed.to_dict())

    @commands.command(brief='Make the catalog with existing entries.', hidden=True)
    @commands.is_owner()
    async def make(self, ctx):
        items = self.data['catalog']['items']
        for item in self.data['catalog']['items'].values():
            embed = await self.make_embed(item)
            channel = self.bot.get_channel(CATALOG_CHANNEL)
            message = await channel.send(embed=embed)
            item['message'] = message.id

    async def make_embed(self, item: dict):
        embed = discord.Embed(title=item.get('link'), url=item.get("link"), color=0xC1CCE6)
        embed.set_author(name=f'Quiet Catalog: Item {item.get("index")}', url=item.get('rym', ''), icon_url='https://cdn.discordapp.com/attachments/562564068376969217/563897825604272137/sonemic.png')
        embed.set_image(url=item.get('cover', ''))
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/562564068376969217/563310548087996426/bookmark.png')

        embed.add_field(name='Artist', value=f'{item.get("artist", "[missing]")}', inline=True)
        embed.add_field(name='Title', value=f'{item.get("title", "[missing]")}', inline=True)
        embed.add_field(name='Year', value=f'{item.get("year", "[missing]")}', inline=True)
        embed.add_field(name='Genre', value=f'{item.get("genre", "[missing]")}', inline=True)
        embed.add_field(name='Average Rating', value=round(item.get("average", 0.00),2), inline=True)
        embed.add_field(name='Ratings', value=len(item["ratings"]), inline=True)

        embed.set_footer(text=f'Catalogged by {self.bot.get_user(item["archiver"]).name} on {item.get("date")}.', icon_url=self.bot.get_user(item["archiver"]).avatar_url)
        return embed
   

def setup(bot):
    bot.add_cog(Catalog(bot, data))