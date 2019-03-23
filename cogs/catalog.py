import discord
import time

from discord.ext import commands
from datetime import datetime

from bot import data


class Catalog(commands.Cog, name='catalog', command_attrs=dict(hidden=False)):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.command(brief='Join the @intercom role to get pings when new items are added to the Quiet Catalog.')
    async def join(self, ctx):
        role = discord.utils.get(ctx.message.guild.roles, name='Intercom')
        await ctx.message.author.add_roles(role)
        await ctx.send('You\'ve been given the @Intercom role.')

    @commands.command(brief='Add an item to the Quiet Catalog.')
    async def add(self, ctx, *, album):
        # check if user has a pass
        the_pass = self.data['users'][str(ctx.message.author.id)]['inventory'].pop("Intercom Pass", None)

        if the_pass is None:
            return await ctx.send('You do not have an Intercom Pass. Purchase one from the Corridor Shop.')
            
        self.data['shop']['items']['Intercom Pass']['stock'] += 1

        # make sure the pass hasn't expired
        now = time.time()
        if (now-the_pass['timestamp']) > 604800:
            return await ctx.send('Your Intercom Pass has expired. It has been removed from your inventory and placed back in the Corridor Shop.')
        
        self.data['catalog']['entries'] += 1
        index = str(self.data['catalog']['entries']).zfill(3)
        now = datetime.now()
        date = now.strftime('%m/%d/%Y')
        self.data['catalog'][index] = {"link": album, "archiver": ctx.message.author.id, "date": date, "ratings": {}, "complete": "false"}

        intercom = self.bot.get_channel(556688777700048907)
        role = discord.utils.get(ctx.message.guild.roles, name='Intercom')
        message = await intercom.send(f'{role.mention}\n**{ctx.author.mention} has used an Intercom Pass!**\nLink: {album}\nPlease react appropriately to this message to indicate your availability to listen.')
        await message.add_reaction('\U0001F44D')
        await message.add_reaction('\U0001F44E')

    @commands.command(brief='Rate an album in the Quiet Catalog.')
    async def rate(self, ctx, index: str, rating: int):
        if index == "current":
            index = str(self.data['catalog']['entries']).zfill(3)

        if rating < 1 or rating  > 10:
            return await ctx.send('The rating you gave is invalid.')
        
        ratings = self.data['catalog'][index]['ratings']
        
        ratings[str(ctx.message.author.id)] = rating

        # update the average
        keys = ratings.keys()
        avg = 0
        for key in keys:
            avg += ratings[key]
        avg /= len(ratings)
        self.data['catalog'][index]['average'] = avg

        await ctx.send(f'Updated your rating for Quiet Catalog item {index}.')
    
    @commands.command(brief='Search the Quiet Catalog by index.')
    async def index(self, ctx, index: str):
        if index == "current":
            index = str(self.data['catalog']['entries']).zfill(3)
        
        if index not in self.data['catalog']:
            await ctx.send(f'Item {index} doesn\'t exist in the catalog.')
        
        item = dict(self.data['catalog'][index])

        embed = discord.Embed(title=item.get('link'), url=item.get('link'), color=0xC1CCE6)
        embed.set_author(name=f'Quiet Catalog: Item {index}', url=item.get('rym', ''))
        embed.set_image(url=item.get('cover', ''))
        embed.add_field(name='Artist', value=f'{item.get("artist", "[missing]")}', inline=True)
        embed.add_field(name='Title', value=f'{item.get("title", "[missing]")}', inline=True)
        embed.add_field(name='Year', value=f'{item.get("year", "[missing]")}', inline=True)
        embed.add_field(name='Genre', value=f'{item.get("genre", "[missing]")}', inline=True)
        embed.add_field(name='Average Rating', value=round(item.get('average', 0.00),2), inline=True)
        embed.add_field(name='Ratings', value=len(item['ratings']), inline=True)
        embed.set_footer(text=f'Catalogged by {self.bot.get_user(item["archiver"]).name} on {item.get("date")}.')

        await ctx.send(embed=embed)

    @commands.command(brief='Search the Quiet Catalog by artist, title, year, genre, or average rating.')
    async def search(self, ctx, search: str, *args):
        searches = set(['artist', 'title', 'year', 'genre', 'average'])
        if search not in searches:
            return await ctx.send(f'You gave an invalid search key. Valid keys are: `{searches}`')

        catalog = dict(self.data['catalog'])
        catalog.pop('entries')

        matches = []
        for key, value in catalog.items():
            print(key, value)
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
        elif len(matches) is 1:
            await ctx.send('Exactly one match found:')
            await ctx.invoke(self.bot.get_command('index'), index=matches[0])
        else:
            await ctx.send(f'{str(len(matches))} matches found:\n`{", ".join(matches)}`')

    @commands.command(brief='Update an item in the Quiet Catalog.')
    async def update(self, ctx, index: str, field: str, data: str):
        fields = set(['artist', 'title', 'year', 'genre', 'rym', 'cover', 'complete'])
        if field not in fields:
            return await ctx.send(f'You gave an invalid field to update. Valid fields are: `{fields}`')

        if index == "current":
            index = str(self.data['catalog']['entries']).zfill(3)

        self.data['catalog'][index][field] = data

        self.data['users'][str(ctx.message.author.id)]['money'] += 1.00

        await ctx.send(f'Updated item {index}\'s `{field.upper()}` field to `{data}`.')

    @commands.command(brief='Get a list of unfinsihed items in the Quiet Catalog.')
    async def work(self, ctx):
        items = dict(self.data["catalog"])
        items.pop("entries")
        keys = items.keys()
        incomplete = []
        for key in keys:
            if items[key]["complete"] == "false":
                incomplete.append(key)

        if not incomplete:
            await ctx.send('No work to do right now!')
        else:
            await ctx.send(f'The following items have not been marked as complete and may be missing information:\n`{", ".join(incomplete)}`')
   
def setup(bot):
    bot.add_cog(Catalog(bot, data))