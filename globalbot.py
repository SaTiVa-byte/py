import asyncio
import json
import math
import os
import sqlite3
import random
import re


import discord
import numpy as np
import pytz
from discord import Guild, Message, TextChannel, Permissions, Member
from discord.ext import commands
from datetime import datetime, timedelta

bot = commands.Bot(command_prefix='=', intents=discord.Intents.all(), case_insensitive=True, help_command=None)


#########################################

# File
if os.path.isfile("servers.json"):
    with open('servers.json', encoding='utf-8') as f:
        servers = json.load(f)
else:
    servers = {"servers": [], "ranks": [], "users": [], "bans": []}
    with open('servers.json', 'w') as f:
        json.dump(servers, f, indent=4)

# Database
con = sqlite3.connect('global.db')
sql = con.cursor()

# Create table
sql.execute('''CREATE TABLE IF NOT EXISTS users (clientid bigint(13) PRIMARY KEY, messages bigint(13) DEFAULT 0, xp bigint(13) 
DEFAULT 0, since DATETIME DEFAULT CURRENT_TIMESTAMP)''')
sql.execute('''CREATE TABLE IF NOT EXISTS ranks (id INTEGER PRIMARY KEY AUTOINCREMENT, rank VARCHAR(45), level int(3) 
DEFAULT 0)''')
con.commit()


#########################################


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.guild is None:
        return
    if str(message.content).startswith('=addnexus'):
        if not guild_exists(message.guild.id):
            server = {
                "guildid": message.guild.id,
                "channelid": message.channel.id,
                "invite": '',
                "verified": False,
                "links": []
            }
            servers["servers"].append(server)
            with open('servers.json', 'w') as f:
                json.dump(servers, f, indent=4)
            embed = discord.Embed(title="**Willkommen im Nexus-Chat von CryLove**",
                                  description="Dein Server ist einsatzbereit!"
                                              " Ab jetzt werden alle Nachrichten in diesem Channel direkt an alle"
                                              " {0} anderen Server weitergeleitet!".format(int(count_guilds()) - 1),
                                  color=0x2ecc71)
            embed.set_thumbnail(url="https://i.giphy.com/media/OkJat1YNdoD3W/source.gif")
            embed.add_field(name='Wie geht es weiter?', value='Du kannst nun deinen eigenen permanenten Invite'
                                                              'link mit `=nexusinvite` hinzufügen.'
                                                              '\r\nAußerdem kannst du mit `=nexuslink <text>'
                                                              ' <url>` bis zu 5 weitere Links hinzufügen.')
            icon_url = "https://cdn.discordapp.com/attachments/896133877083553832/922516636345466920/gaming-logo-template-with-a-ninja-character-2718o-2931_2.png"

            icon = message.guild.icon_url
            if icon:
                icon_url = icon
            embed.set_footer(text='Bitte beachte, dass im Nexus-Chat stets ein Slowmode von mindestens 5 Sekunden'
                                  ' gesetzt sein sollte.', icon_url=icon_url)
            await message.channel.send(embed=embed)

            welcomer = discord.Embed(title='Neuer Nexus-Chat registriert!',
                                     description=f'Ab heute heißen wir {message.guild.name} und seine {len(message.guild.members)} User Herzlich Willkommen!',
                                     color=0x00a8ff)
            icon_url = "https://cdn.discordapp.com/attachments/896133877083553832/922516636345466920/gaming-logo-template-with-a-ninja-character-2718o-2931_2.png"

            icon = message.guild.icon_url
            if icon:
                icon_url = icon
            welcomer.set_thumbnail(url=icon_url)
            welcomer.set_footer(text='Gesendet von Server {}'.format(message.guild.name), icon_url=icon_url)

            links = '[Offizieller-Support](https://discord.gg/crylove) ║ [Bot Invite](' \
                    'https://discord.com/oauth2/authorize?client_id=906517819087265852&scope=bot&applications' \
                    '.commands&permissions=2148396097)\r\n \r\n '
            welcomer.add_field(name='⠀', value='⠀', inline=False)
            welcomer.add_field(name='Links & Hilfe', value=links, inline=False)

            for server in servers["servers"]:
                guild: Guild = bot.get_guild(int(server["guildid"]))
                if guild:
                    if guild.id is message.guild.id:
                        continue
                    channel: TextChannel = guild.get_channel(int(server["channelid"]))
                    if channel:
                        perms: Permissions = channel.permissions_for(guild.get_member(bot.user.id))
                        if perms.send_messages:
                            if perms.embed_links and perms.attach_files and perms.external_emojis:
                                await channel.send(embed=welcomer)
                            else:
                                await channel.send('Es fehlen einige Berechtigungen. '
                                                   '`Nachrichten senden` `Links einbetten` `Datein anhängen`'
                                                   '`Externe Emojis verwenden`')
        else:
            embed = discord.Embed(description="Du hast bereits einen Nexus-Chat auf deinem Server.\r\n"
                                              "Bitte beachte, dass jeder Server nur einen Nexus-Chat besitzen kann.",
                                  color=0x2ecc71)
            await message.channel.send(embed=embed)
        return
    elif str(message.content).startswith('=removenexus'):
        if guild_exists(message.guild.id):
            planetid = get_planet_id(message.guild.id)
            if planetid != -1:
                servers["servers"].pop(planetid)
                with open('servers.json', 'w') as f:
                    json.dump(servers, f, indent=4)
            embed = discord.Embed(title="**Auf Wiedersehen!**",
                                  description="Der Nexus-Chat wurde entfernt. Du kannst ihn jederzeit mit"
                                              " `=addnexus` neu hinzufügen\r\n"
                                              "\r\nWir würden uns über ein [Feedback](https://discord.gg/nexus)"
                                              " von dir freuen!",
                                  color=0x2ecc71)
            await message.channel.send(embed=embed)
        else:
            embed = discord.Embed(description="Du hast noch keinen Nexus-Chat auf deinem Server.\r\n"
                                              "Füge einen mit `=addnexus` in einem frischen Channel hinzu.",
                                  color=0x2ecc71)
            await message.channel.send(embed=embed)
        return
    elif str(message.content).startswith('=nexusinvite'):
        if guild_exists(message.guild.id):
            planetid = get_planet_id(message.guild.id)
            if planetid:
                invite = f'{(await message.channel.create_invite(reason="PlanetInvite")).url}'
                servers["servers"][planetid]["invite"] = invite
                with open('servers.json', 'w') as f:
                    json.dump(servers, f, indent=4)
                embed = discord.Embed(description="Invite hinzugefügt.\r\n"
                                                  "Wenn du Fragen zum Bot hast wende dich bitte an das"
                                                  " [Offizieller-Support](https://discord.gg/nexus) Team.",
                                      color=0x2ecc71)
                await message.channel.send(embed=embed)
        else:
            embed = discord.Embed(description="Du hast noch keinen Nexus-Chat auf deinem Server.\r\n"
                                              "Füge einen mit `=addnexus` in einem frischen Channel hinzu.",
                                  color=0x2ecc71)
            await message.channel.send(embed=embed)
        return
    elif str(message.content).startswith('=nexuslink'):
        if guild_exists(message.guild.id):
            planetid = get_planet_id(message.guild.id)
            if planetid:
                args = message.content.split(' ')
                if len(args) == 3:
                    name = args[1]
                    link = args[2]
                    if not link.startswith('http'):
                        embed = discord.Embed(description="Bitte gebe einen echten Link an.\r\n"
                                                          "Wenn du Fragen zum Bot hast wende dich bitte an das"
                                                          " [Offizieller-Support](https://discord.gg/crylove) Team.",
                                              color=0x2ecc71)
                        await message.channel.send(embed=embed)
                        return
                    linkObj = {
                        "name": name,
                        "url": link
                    }
                    links = servers["servers"][planetid]["links"]
                    if len(links) >= 5:
                        embed = discord.Embed(
                            description="Du hast noch bereits das Maximum an Links zu deinem Server hinzugefügt.\r\n"
                                        "Lösche einen bestehenden Link mit `=nexuslink <text>`.",
                            color=0x2ecc71)
                        await message.channel.send(embed=embed)
                        return
                    links.append(linkObj)
                    servers["servers"][planetid]["links"] = links
                    with open('servers.json', 'w') as f:
                        json.dump(servers, f, indent=4)

                    embed = discord.Embed(description="Link hinzugefügt.\r\n"
                                                      "Wenn du Fragen zum Bot hast wende dich bitte an das"
                                                      " [Offizieller-Support](https://discord.gg/crylove) Team.",
                                          color=0x2ecc71)
                    await message.channel.send(embed=embed)
                elif len(args) == 2:
                    name = args[1]
                    links = servers["servers"][planetid]["links"]
                    linkId = -1
                    i = 0
                    for link in links:
                        if name == link["name"]:
                            linkId = i
                        i += 1
                    if linkId != -1:
                        links.pop(linkId)
                        servers["servers"][planetid]["links"] = links
                        with open('servers.json', 'w') as f:
                            json.dump(servers, f, indent=4)
                        embed = discord.Embed(description="Link gelöscht.\r\n"
                                                          "Wenn du Fragen zum Bot hast wende dich bitte an das"
                                                          " [Offizieller-Support](https://discord.gg/crylove) Team.",
                                              color=0x2ecc71)
                        await message.channel.send(embed=embed)
                    else:
                        embed = discord.Embed(description="Link mit diesem Namen nicht gefunden.\r\n"
                                                          "Wenn du Fragen zum Bot hast wende dich bitte an das"
                                                          " [Offizieller-Support](https://discord.gg/crylove) Team. ",
                                              color=0x2ecc71)
                        await message.channel.send(embed=embed)
                else:
                    embed = discord.Embed(description="Bitte benutze `=nexuslink <text> <url>`\r\n"
                                                      "Wenn du Fragen zum Bot hast wende dich bitte an das"
                                                      " [Offizieller-Support](https://discord.gg/crylove) Team.",
                                          color=0x2ecc71)
                    await message.channel.send(embed=embed)
        else:
            embed = discord.Embed(description="Du hast noch keinen Nexus-Chat auf deinem Server.\r\n"
                                              "Füge einen mit `=addnexus` in einem frischen Channel hinzu.",
                                  color=0x2ecc71)
            await message.channel.send(embed=embed)
        return
    if str(message.content).startswith('=invite'):
        de = pytz.timezone('Europe/Berlin')
        embed = discord.Embed(title="> Invite von **Nexus**",
                              description="Du kannst den Bot [hier](https://discord.com/oauth2/authorize?client_id"
                                          "=906517819087265852&scope=bot&applications.commands&permissions=2148396097"
                                          ") zu deinem eigenen Server einladen.",
                              mestamp=datetime.now().astimezone(tz=de),
                              color=0x2ecc71)
        icon_url = "https://cdn.discordapp.com/attachments/896133877083553832/922516636345466920/gaming-logo-template-with-a-ninja-character-2718o-2931_2.png"
        icon = message.author.avatar_url
        if icon:
            icon_url = icon
        embed.set_footer(text=f'Angefordert von {message.author.name} • {message.author.id}', icon_url=icon_url)
        await message.channel.send(embed=embed)
        return
    if str(message.content).startswith('=help'):
        de = pytz.timezone('Europe/Berlin')
        embed = discord.Embed(title="> 🔹 Hilfe zu **Nexus** 🔹",
                              description='*=addnexus* - Fügt den Nexus-Chat (Global) hinzu.\r\n '
                                          '*=removenexus* - Entfernt den Nexus-Chat\r\n '
                                          '*=nexusinvite* - Füge deinen Invitecode hinzu\r\n '
                                          '*=nexuslink <text> <link>* - Füge bis zu 5 Links hinzu\r\n '
                                          '*=userinfo <user>* - Zeigt die Level und Infos zu dem User\r\n '
                                          '*=top* - Zeigt dir die Bestenliste an\r\n '
                                          '*=invite* - Gibt dir einen Bot Einladungscode zurück',
                              timestamp=datetime.now().astimezone(tz=de),
                              color=0x2ecc71)
        embed.set_thumbnail(url='https://media1.tenor.com/images/6eaab0d39bd1afa7be8985eb7ac2d28b/tenor.gif')
        icon_url = "https://cdn.discordapp.com/attachments/896133877083553832/922516636345466920/gaming-logo-template-with-a-ninja-character-2718o-2931_2.png"
        icon = message.author.avatar_url
        if icon:
            icon_url = icon
        embed.set_footer(text=f'Angefordert von {message.author.name} • {message.author.id}', icon_url=icon_url)
        await message.channel.send(embed=embed)
        return
    if str(message.content).startswith('=userinfo') or str(message.content).startswith('.level'):
        mentions = message.mentions
        if len(mentions) == 1:
            user: Member = mentions[0]
            await send_userinfo(message, user)
            return
        else:
            await send_userinfo(message, message.author)
            return
    if str(message.content).startswith('=top') or str(message.content).startswith('.leaderboard'):
        await send_top(message)
    if str(message.content).startswith('=ban'):
        if 0 <= get_Rank(message.author.id) <= 2:
            args = message.content.split(' ')
            if len(args) == 2:
                user = args[1]
                servers["bans"].append(user)
                with open('servers.json', 'w') as f:
                    json.dump(servers, f, indent=4)
                de = pytz.timezone('Europe/Berlin')
                embed = discord.Embed(description="User wurde gebannt!",
                                      mestamp=datetime.now().astimezone(tz=de),
                                      color=0x2ecc71)
                icon_url = "https://cdn.discordapp.com/attachments/896133877083553832/922516636345466920/gaming-logo-template-with-a-ninja-character-2718o-2931_2.png"
                icon = message.author.avatar_url
                if icon:
                    icon_url = icon
                embed.set_footer(text=f'Moderiert von {message.author.name} • {message.author.id}', icon_url=icon_url)
                mess = await message.channel.send(embed=embed)
                await mess.add_reaction('a:ban:918585871966568500')
            await message.delete()
            return
    if str(message.content).startswith('=unban'):
        if 0 <= get_Rank(message.author.id) <= 2:
            args = message.content.split(' ')
            if len(args) == 2:
                user = args[1]
                index = 0
                for id in servers["bans"]:
                    if user == id:
                        servers["bans"].pop(index)
                        with open('servers.json', 'w') as f:
                            json.dump(servers, f, indent=4)
                        de = pytz.timezone('Europe/Berlin')
                        embed = discord.Embed(description="User wurde Entbannt!",
                                              mestamp=datetime.now().astimezone(tz=de),
                                              color=0x2ecc71)
                        icon_url = "https://cdn.discordapp.com/attachments/896133877083553832/922516636345466920/gaming-logo-template-with-a-ninja-character-2718o-2931_2.png"
                        icon = message.author.avatar_url
                        if icon:
                            icon_url = icon
                        embed.set_footer(text=f'Moderiert von {message.author.name} • {message.author.id}',
                                         icon_url=icon_url)
                        mess = await message.channel.send(embed=embed)
                        await mess.add_reaction('a:entfernt:918586039566729317')
                        await message.delete()
                        return
                    index += 1
                de = pytz.timezone('Europe/Berlin')
                embed = discord.Embed(description="User ist nicht gebannt.",
                                      mestamp=datetime.now().astimezone(tz=de),
                                      color=0x2ecc71)
                icon_url = "https://cdn.discordapp.com/attachments/896133877083553832/922516636345466920/gaming-logo-template-with-a-ninja-character-2718o-2931_2.png"
                icon = message.author.avatar_url
                if icon:
                    icon_url = icon
                embed.set_footer(text=f'Moderiert von {message.author.name} • {message.author.id}', icon_url=icon_url)
                mess = await message.channel.send(embed=embed)
                await mess.add_reaction('a:entfernt:918586039566729317')
            await message.delete()
            return
    if get_planet(message.guild.id, message.channel.id):
        if message.content.startswith("=") and len(message.content) > 2:
            await message.delete()
            return
        if not is_banned(message.author.id):
            await sendAll(message)
            xp = random.randint(1, 5)
            t = (xp, message.author.id,)
            sql.execute('UPDATE users SET xp = xp + ?, messages = messages + 1 WHERE clientid=?', t)
            con.commit()
        else:
            embed = discord.Embed(description='{0} du wurdest aus dem Nexus-Chat Global gebannt. \r\n'
                                              'Du kannst [hier](https://discord.gg/crylove) einen'
                                              ' Entbannungsantrag in <#925111886062714900> stellen.'
                                  .format(message.author.mention),
                                  color=0x2ecc71)
            await message.channel.send(embed=embed)


#########################################

async def sendAll(message: Message):
    content = message.content.strip()
    content = content.replace("⠀", " ")
    while "  " in content:
        content = content.replace("  ", " ")

    author = message.author
    xp = 0
    xpload = get_xp(author.id)
    if xpload is not None:
        xp = xpload
    else:
        t = (message.author.id,)
        sql.execute('INSERT INTO users(clientid) VALUES(?)', t)
        con.commit()
        xp = get_xp(author.id)

    attachments = message.attachments
    de = pytz.timezone('Europe/Berlin')
    embed = discord.Embed(description=content, timestamp=datetime.now().astimezone(tz=de), color=author.color)
    rank = get_Rank(author.id)

    if rank != -1:
        rankjson = servers["ranks"][rank]
        ranktext = f'{rankjson["name"]} {rankjson["icon"]}'
        embed.title = ranktext

    level = to_level(xp)
    icon = author.avatar_url
    embed.set_author(
        name=f'◆{get_rank_for_xp(level)}◆ Level {level} • {xp} XP\r\n  》 {author.name}#{author.discriminator} 《',
        icon_url=icon)

    icon_url = "https://cdn.discordapp.com/attachments/896133877083553832/922516636345466920/gaming-logo-template-with-a-ninja-character-2718o-2931_2.png"
    icon = message.guild.icon_url
    if icon:
        icon_url = icon
    embed.set_thumbnail(url=icon_url)
    embed.set_footer(text='Gesendet von Server {}'.format(message.guild.name), icon_url=icon_url)

    links = '[Offizieller-Support](https://discord.gg/crylove) ║ '
    planet = get_planet(message.guild.id, message.channel.id)
    if len(planet["invite"]) > 0:
        invite = planet["invite"]
        emoji = ''
        if 'discord.gg' not in invite:
            invite = 'https://discord.gg/{}'.format(invite)
        if planet["verified"]:
            emoji = ' <a:verified:918585780606238731>'
        links += '[Server Invite]({0}){1} ║ '.format(invite, emoji)
    links += f'[Bot-Invite](https://discord.com/oauth2/authorize?client_id=906517819087265852&scope=bot&applications' \
             f'.commands&permissions=2148396097) ║ [Bot-Vote](https://top.gg/bot/906517819087265852/vote)\r\n \r\n '

    for link in planet["links"]:
        links += '[{0}]({1}) | '.format(link["name"], link["url"])

    if links.endswith("| "):
        links = links[:-2]

    embed.add_field(name='⠀', value='⠀', inline=False)
    embed.add_field(name=f'Links & Hilfe • {message.author.id}', value=links, inline=False)

    if len(attachments) > 0:
        img = attachments[0]
        embed.set_image(url=img.url)

    for server in servers["servers"]:
        guild: Guild = bot.get_guild(int(server["guildid"]))
        if guild:
            channel: TextChannel = guild.get_channel(int(server["channelid"]))
            if channel:
                perms: Permissions = channel.permissions_for(guild.get_member(bot.user.id))
                if perms.send_messages:
                    if perms.embed_links and perms.attach_files and perms.external_emojis:
                        await channel.send(embed=embed)
                    else:
                        await channel.send('{0}: {1}'.format(author.name, content))
                        await channel.send('Es fehlen den Nexus Einige Berechtigungen. '
                                           '`Nachrichten senden` `Links einbetten` `Datein anhängen`'
                                           '`Externe Emojis verwenden`')
    await message.delete()


async def send_userinfo(message: Message, user: Member):
    xp = 0
    xpload = get_xp(user.id)
    if xpload is not None:
        xp = xpload
    else:
        t = (user.id,)
        sql.execute('INSERT INTO users(clientid) VALUES(?)', t)
        con.commit()
        await asyncio.sleep(1)
        xp = get_xp(user.id)
    level = to_level(xp)
    xpToLevel = for_level(level + 1) - xp
    de = pytz.timezone('Europe/Berlin')
    embed = discord.Embed(title=f"> Userinfo zu {user.display_name}",
                          description='',
                          timestamp=datetime.now().astimezone(tz=de),
                          color=0x00a8ff)
    embed.add_field(name='Name', value=f'```{user.name}#{user.discriminator}```', inline=True)
    embed.add_field(name='XP', value=f'```{xp}```', inline=True)
    embed.add_field(name='Level', value=f'```{level}```', inline=True)
    embed.add_field(name='Benötigte XP', value=f'```{int(xpToLevel)}```', inline=True)
    embed.add_field(name='Messages', value=f'```{get_messages(user.id)}```', inline=True)
    embed.add_field(name='Nexus-User seit', value=f'```{get_since(user.id)}```', inline=True)
    icon = message.author.avatar_url
    if icon:
        icon_url = icon
    embed.set_footer(text=f'Angefordert von {message.author.name} • {message.author.id}', icon_url=icon_url)
    await message.channel.send(embed=embed)


async def send_top(message: Message):
    de = pytz.timezone('Europe/Berlin')
    embed = discord.Embed(title=f"> Globale Bestenliste 🏆",
                          description=get_toplist(),
                          timestamp=datetime.now().astimezone(tz=de),
                          color=0x00a8ff)
    embed.set_thumbnail(url='https://media1.tenor.com/images/2a8c16ba3bac31f0e39648de78e14406/tenor.gif?itemid=4115631')
    icon = message.author.avatar_url
    if icon:
        icon_url = icon
    embed.set_footer(text=f'● Angefordert von {message.author.name} • {message.author.id}', icon_url=icon_url)
    await message.channel.send(embed=embed)


#########################################


def guild_exists(guildid):
    for server in servers["servers"]:
        if int(server["guildid"]) == int(guildid):
            return True
    return False


def count_guilds():
    return len(servers["servers"])


def get_planet(guild_id, channelid=None):
    planet = None
    for server in servers["servers"]:
        if int(server["guildid"]) == int(guild_id):
            if channelid:
                if int(server["channelid"]) == int(channelid):
                    planet = server
            else:
                planet = server
    return planet


def get_planet_id(guild_id):
    planet = -1
    i = 0
    for server in servers["servers"]:
        if int(server["guildid"]) == int(guild_id):
            planet = i
        i += 1
    return planet


def is_banned(clientid):
    if str(clientid) in servers["bans"]:
        return True
    else:
        return False


def get_xp(clientid):
    t = (clientid,)
    sql.execute('SELECT xp FROM users WHERE clientid=?', t)
    xp = sql.fetchone()
    if xp is None:
        return None
    else:
        return xp[0]


def get_rank_for_xp(level: int):
    t = (level,)
    sql.execute('SELECT rank FROM ranks WHERE level<=? ORDER BY level DESC LIMIT 1', t)
    rank = sql.fetchone()
    if rank is None:
        return "Reisender"
    else:
        return rank[0]


def get_messages(clientid):
    t = (clientid,)
    sql.execute('SELECT messages FROM users WHERE clientid=?', t)
    messages = sql.fetchone()
    if messages is None:
        return None
    else:
        return messages[0]


def get_since(clientid):
    t = (clientid,)
    sql.execute('SELECT since FROM users WHERE clientid=?', t)
    since = sql.fetchone()
    if since is None:
        return None
    else:
        return since[0]


def to_level(xp: int):
    return int((xp / 100.0) ** 0.6)


def for_level(level: int):
    return math.exp(np.log(level) / 0.6) * 100


def get_toplist():
    toplist = ""
    sql.execute("SELECT clientid, messages, xp as rank FROM users ORDER BY xp DESC LIMIT 10")
    top = sql.fetchall()
    rank = 1
    for row in top:
        if not len(row) == 3:
            continue
        clientid = row[0]
        messages = row[1]
        xp = row[2]
        level = to_level(xp)
        toplist += f"**{rank}.** <@{clientid}> `⌊{get_rank_for_xp(level)}⌉ Level {level} • {xp} XP • {messages} Nachrichten`\r\n"
        rank += 1
    return toplist


def get_Rank(clientid):
    rankid = -1
    for user in servers["users"]:
        if int(user["clientid"]) == int(clientid):
            rank = int(user["rank"])
            if servers["ranks"][rank]:
                return rank
    melion: Guild = bot.get_guild(guild id)
    user: Member = melion.get_member(clientid)
    if user is None:
        return rankid
    if melion.get_role(booster role) in user.roles:
        return 3
    return rankid



#########################################


@bot.event
async def on_ready():
    print('Eingeloggt als')
    print(bot.user.name)
    print(bot.user.id)
    print('Nexus')
    print(f'Ich bin auf {len(bot.guilds)} guilds')
    print(f'Invite: https://discord.com/oauth2/authorize?client_id={bot.user.id}&scope=bot&applications.commands'
          f'&permissions=2148396097')
    bot.loop.create_task(status_task())


async def status_task():
    while True:
        await bot.change_presence(activity=discord.Game('discord.gg/crylove'), status=discord.Status.online)
        await asyncio.sleep(30)
        await bot.change_presence(activity=discord.Game('Nexus-Global'), status=discord.Status.online)
        await asyncio.sleep(30)


#########################################

bot.run("token")
