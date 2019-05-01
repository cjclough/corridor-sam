# -*- coding: utf-8 -*-
import discord
import json
import random

from discord.ext import commands


class Roles(commands.Cog, name='Roles', command_attrs=dict(hidden=True)):
    def __init__(self, bot):
        self.bot = bot

    async def update_menu(self, ctx, menu, menu_name, menu_id):
        emojis = menu['roles'].keys()
        roles = menu['roles'].values()
        text = ''
        try:
            for role, emoji in zip(roles, emojis):
                text += f'\n\n{emoji}: **`{role}`**'
        except Exception:
            pass

        # edit the message with the updated embed
        embed = discord.Embed(title=f'**Role Menu: {menu_name.upper()}**', url=menu.get('rym', ''), color=0xC1CCE6)
        embed.set_thumbnail(url=menu.get('icon', ''))
        embed.add_field(name='React to give yourself a role.', value=text, inline=True)

        await self.bot.http.edit_message(menu_id, ctx.message.channel.id, embed=embed.to_dict())
        for emoji in emojis:
            await self.bot.http.add_reaction(menu_id, ctx.message.channel.id, emoji)
        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if not payload.guild_id: return

        with open('./config/role_menus.json', 'r+') as f:
            menus = json.load(f)

        # find the name of the menu, if it exists
        name = None
        for key, value in menus['ids'].items():
            if value == payload.message_id:
                name = key
                break
                
        if not name: return

        roles = dict(menus['menus'][name]['roles'].items())
        
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = discord.utils.get(guild.roles, name=roles[payload.emoji.name])
        if role is None:
            role = await guild.create_role(name=roles[payload.emoji.name], mentionable=True)

        await member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if not payload.guild_id: return

        with open('./config/role_menus.json', 'r+') as f:
            menus = json.load(f)

        # find the name of the menu, if it exists
        name = None
        for key, value in menus['ids'].items():
            if value == payload.message_id:
                name = key
                break

        if not name: return

        roles = menus['menus'][name].get('roles')
        
        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = discord.utils.get(guild.roles, name=roles[payload.emoji.name])

        await member.remove_roles(role)

    @commands.command(brief='Register a new role menu.')
    @commands.has_any_role('Lead', 'Supervisor')
    async def register(self, ctx, name: str):
        with open('./config/role_menus.json', 'r+') as f:
            menus = json.load(f)
        
        embed = discord.Embed(title=f'**Role Menu: {name.upper()}**', color=0xC1CCE6)
        embed.add_field(name='React to give yourself a role.', value='Empty menu', inline=True)

        message = await ctx.send(embed=embed)

        try:
            menus['menus'][name] = {"roles": {}}
        except KeyError:
            menus['menus'] = {name: {"roles": {}}}

        try:
            menus['ids'][name] = message.id
        except KeyError:
            menus['ids'] = {name: message.id}

        with open('./config/role_menus.json', 'w') as f:
            json.dump(menus, f, indent=4)

        await ctx.message.delete()

    @commands.command(brief='Add a role to a registered menu.')
    @commands.has_any_role('Lead', 'Supervisor')
    async def addrole(self, ctx, menu_name: str, role: str, emoji: str):
        with open('./config/role_menus.json', 'r') as f:
                menus = json.load(f)

        if menu_name not in menus['menus']:
            return await ctx.send(f'{menu_name} is not a registered menu. To view all registered menus, do `.view all`.')

        menus['menus'][menu_name]['roles'][emoji] = role.title()

        with open('./config/role_menus.json', 'w') as f:
            json.dump(menus, f, indent=4)

        await self.update_menu(ctx, menus['menus'][menu_name], menu_name, menus['ids'].get(menu_name))

    @commands.command(brief='Edit a role.')
    @commands.has_any_role('Lead', 'Supervisor')
    async def editrole(self, ctx, menu_name: str, old_role: str, old_emoji: str, new_role: str, new_emoji: str):
        with open('./config/role_menus.json', 'r') as f:
                menus = json.load(f)

        if menu_name not in menus['menus']:
            return await ctx.send(f'{menu_name} is not a registered menu.')

        menus['menus'][menu_name]['roles'][new_emoji] = menus['menus'][menu_name]['roles'].pop(old_emoji)
        menus['menus'][menu_name]['roles'][new_emoji] = new_role.title()

        with open('./config/role_menus.json', 'w') as f:
            json.dump(menus, f, indent=4)

        await self.update_menu(ctx, menus['menus'][menu_name], menu_name, menus['ids'].get(menu_name))

    @commands.command(brief='Add an icon to a registered menu.')
    @commands.has_any_role('Lead', 'Supervisor')
    async def addicon(self, ctx, menu_name: str, icon: str):
        with open('./config/role_menus.json', 'r') as f:
                menus = json.load(f)

        if menu_name not in menus['menus']:
            return await ctx.send(f'{menu_name} is not a registered menu.')
        menus['menus'][menu_name]['icon'] = icon

        with open('./config/role_menus.json', 'w') as f:
            json.dump(menus, f, indent=4)

        await self.update_menu(ctx, menus['menus'][menu_name], menu_name, menus['ids'].get(menu_name))

    @commands.command(brief='Shuffle the role list.')
    @commands.is_owner()
    async def shuffle(self, ctx):
        guild = ctx.message.guild
        roles = guild.roles
        for role in roles[1:-1]:
            print(role.name)
            await role.edit(position=random.randint(0, len(roles)-1))

    @commands.command(brief='Create role menus from a dictionary.')
    @commands.is_owner()
    async def fromdict(self, ctx, name: str):
        with open('./config/role_menus.json', 'r') as f:
            menus = json.load(f)

        menu = menus['menus'].get(name, None)
        if menu is None:
            return await ctx.send('Invalid menu name.')

        embed = discord.Embed(title=f'**Role Menu: {name.upper()}**', color=0xC1CCE6)
        embed.set_thumbnail(url=menu.get('icon'))

        keys = list(menu['roles'].keys())
        random.shuffle(keys)
        text = ' '
        for emoji in keys:
            text += f'\n\n{emoji}: **`{menu["roles"][emoji]}`**'

        embed.add_field(name='React to give yourself a role.', value=text, inline=True)

        message = await ctx.send(embed=embed)
        
        menus['ids'][name] = message.id

        with open('./config/role_menus.json', 'w') as f:
            json.dump(menus, f, indent=4)

        for emoji in keys:
            await self.bot.http.add_reaction(message.id, ctx.message.channel.id, emoji)

        await ctx.message.delete()


def setup(bot):
    bot.add_cog(Roles(bot))