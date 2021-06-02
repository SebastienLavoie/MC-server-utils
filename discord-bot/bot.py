#!/usr/bin/env python3

import logging
from argparse import ArgumentParser
from configparser import ConfigParser
from pathlib import Path
from subprocess import run, PIPE
from sys import stdout
from typing import Dict, List
from mcstatus import MinecraftServer

import discord
from discord.ext import tasks

response_channel = "server-evenements"

# Logging setup
file_name = Path(__file__).stem
log = logging.getLogger(file_name)

handler = logging.StreamHandler(stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

log.addHandler(handler)
log.setLevel(logging.DEBUG)

log.info("Logging setup")

# Config reading
config = ConfigParser()
config.read(Path.home().joinpath(".config", "discord", "mcserverbot.conf"))

token = config['default']["token"]
online_role_id = int(config["default"]["online_role_id"])
guild_id = config["default"]["guild_id"]
server_log = Path.home().joinpath("minecraft", "create-mod", "server.log")

# Intents
intents = discord.Intents(messages=True, members=True, presences=True, guilds=True)

# Member cache
member_cache = discord.MemberCacheFlags.none()
member_cache.online = True
member_cache.joined = True

# Minecraft server
server = MinecraftServer.lookup("localhost:25565")


class MCServerClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mc_guild = None  # To be populated later on

    @staticmethod
    def online() -> List[str]:
        query = server.query()
        return [p.lower() for p in query.players.names]

    @staticmethod
    def get_ip() -> str:
        return run("dig +short myip.opendns.com @resolver1.opendns.com", shell=True, stdout=PIPE,
                   universal_newlines=True).stdout

    def get_roles(self):
        return self.mc_guild.roles

    def get_online_role(self) -> discord.Role:
        return self.mc_guild.get_role(online_role_id)

    async def get_members_dict(self) -> Dict[str, discord.Member]:
        members = await self.mc_guild.fetch_members().flatten()
        # log.debug(members)
        member_dict = dict()
        for member in members:
            if member.id != self.user.id:
                name = member.nick.lower() if member.nick is not None else member.name.lower()
                member_dict[name] = member
        return member_dict

    @tasks.loop(minutes=1.0)
    async def update_player_status(self):
        players_online = self.online()
        log.debug(f"Players online: {players_online}")
        members_dict = await self.get_members_dict()
        online_role = self.get_online_role()
        log.debug(f"Starting update_player_status task")
        for member in members_dict.keys():
            if member in players_online and online_role not in members_dict[member].roles:
                # log.debug(members_dict[player.lower()].roles)
                log.info(f"Adding role {online_role.name} to {member}")
                await members_dict[member].add_roles(online_role, atomic=True)
            elif online_role in members_dict[member].roles:
                log.info(f"Removing role {online_role.name} from {member}")
                await members_dict[member].remove_roles(online_role, atomic=True)

    async def on_ready(self):
        for guild in self.guilds:
            if guild.id == guild_id:
                break

        self.mc_guild = guild
        log.info(f"{self.user} has connected to guild {guild.name} with id {guild.id}")
        self.update_player_status.start()

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return

        if message.channel.name == response_channel:
            log.debug(f"Received: '{message.content}' from {message.author}")
            if message.content.lower() == "hello":
                msg = "Hello World!"
                log.info(f"Sending: '{msg}'")
                await message.channel.send(msg)
            elif message.content.lower() == "!help":
                msg = "Available commands: !ip, !online"
                log.info(f"Sending: '{msg}'")
                await message.channel.send(msg)
            elif message.content.lower() == "!ip":
                msg = self.get_ip()
                log.info(f"Sending: '{msg}'")
                await message.channel.send(msg)
            elif message.content.lower() == "!online":
                players_online = self.online()
                if len(players_online) == 0:
                    msg = "No one online"
                    log.info(f"Sending: '{msg}'")
                    await message.channel.send(msg)
                else:
                    msg = "Players Online:\n"
                    for player in players_online:
                        msg += f"  - {player}\n"
                    log.info(f"Sending: '{msg}'")
                    await message.channel.send(msg)


argparser = ArgumentParser()
argparser.add_argument("--log-level", type=str, default="DEBUG")
args = argparser.parse_args()

log.setLevel(args.log_level)
client = MCServerClient(member_cache_flags=member_cache, intents=intents)
client.run(token)
