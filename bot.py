# -*- coding: utf-8 -*-
import discord
import json

from discord.ext import commands

# do some set up stuff
with open('./config/config.json') as f:
    config = json.load(f)
token = config['token']

bot = commands.Bot(command_prefix='.')
cogs = ['cogs.sam', 'cogs.owner', 'cogs.shop', 'cogs.last', 'cogs.catalog', 'cogs.moderator']

# open up the data
with open('./config/data.json', 'r') as f:
    data = json.load(f)

if __name__ == '__main__':
    for cog in cogs:
        try:
            bot.load_extension(cog)
        except Exception as error:
            print(f'cog {cog} cannot be loaded. [{error}]')

    bot.run(token)
