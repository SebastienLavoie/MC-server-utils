#!/usr/bin/env python3

import discord
from discord.ext import tasks, commands

import logging
import re
from typing import Dict
from sys import stdout
from configparser import ConfigParser
from pathlib import Path
from subprocess import run, PIPE

num_players = 3
response_channel = "server-evenements"

# Logging setup
file_name = Path(__file__).stem
log = logging.getLogger(file_name)

handler = logging.StreamHandler(stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

log.addHandler(handler)
log.setLevel(logging.DEBUG)

log.info("Logging setup")
# Config reading
config = ConfigParser()
config.read(Path.home().joinpath(".config", "discord", "mcserverbot.conf"))

token = config['default']["token"]
online_role_id = config["default"]["online_role_id"]
guild_id = config["default"]["guild_id"]
server_log = Path.home().joinpath("minecraft", "create-mod", "server.log")

# Intents
intents = discord.Intents(messages=True, members=True, presences=True)

# Member cache
member_cache = discord.MemberCacheFlags.none()
member_cache.online = True
member_cache.joined = True


class MCServerClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mc_guild = None  # To be populated later on
        self.members = None
        self.roles = None

    @staticmethod
    def online() -> Dict[str, bool]:
        players = dict()
        with open(server_log, "r") as fp:
            for line in reversed(fp.readlines()):
                patt = re.match(r"^.*: (.*) (.*) the game", line)
                if patt is not None:
                    if patt.group(1) not in players:
                        if patt.group(2) == "joined":
                            players[patt.group(1)] = True
                        else:
                            players[patt.group(1)] = False
                if len(players) == num_players:
                    break
        return players

    @staticmethod
    def get_ip() -> str:
        return run("dig +short myip.opendns.com @resolver1.opendns.com", shell=True, stdout=PIPE,
                   universal_newlines=True).stdout

    def get_roles(self):
        return self.mc_guild.roles

    def get_online_role(self) -> discord.Role:
        roles = self.roles
        for role in roles:
            if role.id == online_role_id:
                return role

        raise discord.ClientException("Could not find online role in guild!")

    def get_members_dict(self) -> Dict[str, discord.Member]:
        members = self.members
        log.debug(members)
        member_dict = dict()
        for member in members:
            if member.id != self.user.id:
                name = member.nick if member.nick is not None else member.name
                member_dict[name] = member
        return member_dict

    @tasks.loop(minutes=1.0)
    async def update_player_status(self):
        players_online = self.online()
        log.debug(players_online)
        members_dict = self.get_members_dict()
        log.debug(members_dict)
        online_role = self.get_online_role()
        log.debug(f"Starting update_player_status task")

        if len(players_online) == 0:
            return
        else:
            for player, online in players_online.items():
                if player.lower() in members_dict.keys():
                    if online is True:
                        log.info(f"Adding role {online_role.name} to {player}")
                        await members_dict[player.lower()].add_roles(online_role)
                    elif online_role in members_dict[player.lower()].roles and online is False:
                        log.info(f"Removing role {online_role.name} from {player}")
                        await members_dict[player.lower()].remove_roles(online_role)

    async def on_ready(self):
        for guild in self.guilds:
            if guild.id == guild_id:
                break

        self.mc_guild = guild
        log.info(f"{self.user} has connected to guild {guild.name} with id {guild.id}")
        self.members = await self.mc_guild.fetch_members().flatten()
        self.roles = await self.mc_guild.fetch_roles()
        self.update_player_status.start()

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        if message.channel.name == response_channel:
            log.debug(f"Received {message.content} from {message.author}")
            if message.content.lower() == "hello":
                msg = "Hello World!"
                log.info(f"Sending: {msg}")
                await message.channel.send(msg)
            elif message.content.lower() == "!help":
                msg = "Available commands: !ip, !online"
                log.info(f"Sending: {msg}")
                await message.channel.send(msg)
            elif message.content.lower() == "!ip":
                msg = self.get_ip()
                log.info(f"Sending: {msg}")
                await message.channel.send(msg)
            elif message.content.lower() == "!online":
                players = self.online()
                if len(players) == 0:
                    msg = "No one online"
                    log.info(f"Sending: {msg}")
                    await message.channel.send(msg)
                else:
                    msg = ""
                    for player, online in players.items():
                        if online is True:
                            msg += f"{player}\n"
                    msg = "No one online" if len(msg) == 0 else msg
                    log.info(f"Sending: {msg}")
                    await message.channel.send(msg)


client = MCServerClient(member_cache_flags=member_cache, intents=intents)
client.run(token)
