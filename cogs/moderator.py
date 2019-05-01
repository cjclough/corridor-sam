import discord
import asyncio
import json

from discord.ext import commands

from bot import data


class Moderator(commands.Cog, name='Moderation', command_attrs=dict(hidden=False)):
    def __init__(self, bot, data):
        self.bot = bot
        self.data = data

    @commands.Cog.listener()
    async def on_member_join(self, member):
        role = discord.utils.get(member.guild.roles, name='Employee')
        await member.add_roles(role)
        self.data['users'][str(member.id)] = {"member": member.name, "reprimands": 0, "samcoins": 0, "messages": 0, "inventory": {}, "office": {}}
        door = self.bot.get_channel(556682836388872192)
        info = self.bot.get_channel(556686992101081109)
        await door.send(f'Welcome to Quiet Corridor, {member.mention}! Please go to {info.mention} to get started.')

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        await asyncio.sleep(2)
        if member.name != self.data['sam'].get('banned', None):
            door = self.bot.get_channel(556682836388872192)
            await door.send(f'{member.mention} has left Quiet Corridor. :(')

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        self.data['sam']['banned'] = user.name
        self.data['users'].pop(str(user.id))
        door = self.bot.get_channel(556682836388872192)
        await door.send(f'{user.mention} has been fired (banned) from Quiet Corridor.')
        self.data['sam'].pop('banned')

    @commands.command(brief='Delete messages in bulk. Defaults to 100.')
    @commands.has_any_role('Lead', 'Supervisor')
    async def delete(self, ctx, limit=100):
        async for message in ctx.message.channel.history(limit=limit):
            await message.delete()
            await asyncio.sleep(0.5)

    @commands.command(brief='Reprimand an employee.')
    @commands.has_any_role('Lead', 'Supervisor')
    async def reprimand(self, ctx, employee: discord.Member):
        self.data['users'][str(employee.id)]['reprimands'] += 1

        if self.data['users'][str(employee.id)]['reprimands'] == 3:
            ctx.message.guild.ban(employee, delete_message_days=0, reason="Reprimanded three times.")

    @commands.command(brief='Kick an employee from Quiet Corridor.')
    @commands.has_any_role('Lead', 'Supervisor')
    async def kick(self, ctx, employee: discord.Member, *, reason: str=None):
        await employee.kick(employee, reason=reason)

    @commands.command(brief='Ban an employee from Quiet Corridor.')
    @commands.has_any_role('Lead', 'Supervisor')
    async def ban(self, ctx, employee: discord.Member, delete: int=0, *, reason: str=None):
        employee.ban(employee, delete_message_days=delete, reason=reason)

def setup(bot):
    bot.add_cog(Moderator(bot, data))