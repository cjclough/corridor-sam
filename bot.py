# -*- coding: utf-8 -*-
import discord
import json

from discord.ext import commands

CATALOG_CHANNEL = 563836202915069974
USER_AGENT = 'corridor-sam'

# do some set up stuff
with open('./config/config.json') as f:
    config = json.load(f)
token = config['token']

bot = commands.Bot(command_prefix='.')
cogs = ['cogs.sam', 
        'cogs.owner',
        'cogs.shop',
        'cogs.last',
        'cogs.catalog',
        'cogs.moderator',
        'cogs.roles',
        'cogs.backpack',
        'cogs.breakroom',
        'cogs.util']

# open up the data
with open('./config/data.json', 'r') as f:
    data = json.load(f)

# get assets
with open('./config/assets.json', 'r') as f:
    assets = json.load(f)

print(assets)

if __name__ == '__main__':
    for cog in cogs:
        try:
            bot.load_extension(cog)
        except Exception as error:
            print(f'cog {cog} cannot be loaded. [{error}]')

    bot.run(token)