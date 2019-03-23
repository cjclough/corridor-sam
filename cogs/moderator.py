import discord
import asyncio

from discord.ext import commands

from bot import data


class Moderator(commands.Cog, name='moderation', command_attrs=dict(hidden=False)):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.command(brief='Delete messages in bulk. Defaults to 100.')
    @commands.has_any_role('Lead', 'Supervisor')
    async def delete(self, ctx, limit=100):
        async for message in ctx.message.channel.history(limit=limit):
            await message.delete()
            await asyncio.sleep(0.5)

    @commands.command(brief='Reprimand an employee.')
    @commands.has_any_role('Lead', 'Supervisor')
    async def reprimand(self, ctx, employee: str):
        employeeId = employee.strip('<').strip('>').strip('!').strip('@')
        employee = self.bot.getuser(int(employeeId))
        self.data['users'][employeeId]['reprimands'] += 1

        if self.data['users'][employee]['reprimands'] is 3:
            ctx.message.guild.ban(employee, delete_message_days=7)

    
    

def setup(bot):
    bot.add_cog(Moderator(bot, data))