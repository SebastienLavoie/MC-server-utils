#!/usr/bin/env python3

import logging
from argparse import ArgumentParser
from configparser import ConfigParser
from pathlib import Path
from subprocess import run, PIPE
from sys import stdout
from typing import Dict, List
from mcstatus import JavaServer
from traceback import format_exc

import discord
from discord.ext import tasks

response_channel_id = 846077490333614091

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

# Intents
intents = discord.Intents(messages=True, members=True, presences=True, guilds=True, message_content=True)

# Member cache
member_cache = discord.MemberCacheFlags.none()
member_cache.joined = True

# Discord to minecraft name mapping
user_name_override = {"madmike1771": "madmikey1771"}

class MCServerClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mc_guild = None  # To be populated later on
        self.response_channel = None
        self.update_players_loop_count = 0

    @staticmethod
    def online() -> List[str]:
        try:
            server = JavaServer.lookup("localhost:25565")
            status = server.status()
            if status.players.sample is not None:
                return [p.name.lower() for p in status.players.sample]
            else:
                return []
        except Exception as e:
            log.error(e)
            return []

    @staticmethod
    def get_ip() -> str:
        return run("dig +short myip.opendns.com @resolver1.opendns.com", shell=True, stdout=PIPE,
                   universal_newlines=True).stdout

    def get_roles(self):
        return self.mc_guild.roles

    def get_online_role(self) -> discord.Role:
        return self.mc_guild.get_role(online_role_id)

    async def get_members(self):
        return self.mc_guild.fetch_members()

    async def get_members_dict(self) -> Dict[str, discord.Member]:
        members = await self.get_members()
        member_dict = dict()
        try:
            async for member in members:
                if member.id != self.user.id:
                    name = member.nick.lower() if member.nick is not None else member.name.lower()
                    if name in user_name_override.keys():
                        member_dict[user_name_override[name]] = member
                    else:
                        member_dict[name] = member
        except discord.errors.DiscordServerError as e:
            log.error(f"Error connecting to discord server: {e}")
            log.error(format_exc())
            log.error("Committing suicide")
            exit(1)
        return member_dict

    @tasks.loop(seconds=10.0)
    async def update_player_status(self):
        players_online = self.online()
        members_dict = await self.get_members_dict()
        if len(players_online) > 0 and (self.update_players_loop_count % 10) == 0:
            log.debug(f"Players online: {players_online}")
        online_role = self.get_online_role()
        for member in members_dict.keys():
            if (member in players_online) and (
                    online_role not in members_dict[member].roles):
                log.info(f"Adding role {online_role.name} to {member}")
                await members_dict[member].add_roles(online_role, atomic=True)
                # await self.send_msg(f"{member} joined the game")
            elif member not in players_online and online_role in members_dict[member].roles:
                log.info(f"Removing role {online_role.name} from {member}")
                await members_dict[member].remove_roles(online_role, atomic=True)
                # await self.send_msg(f"{member} left the game")
        self.update_players_loop_count += 1

    async def on_ready(self):
        for guild in self.guilds:
            if guild.id == guild_id:
                break

        self.mc_guild = guild
        self.response_channel = self.get_channel(response_channel_id)
        log.info(f"{self.user} has connected to guild {guild.name} with id {guild.id}")
        self.update_player_status.start()

    async def send_msg(self, msg: str):
        log.info(f"Sending: '{msg}'")
        await self.response_channel.send(msg)

    async def on_message(self, message):
        def get_response(rcv_msg: str):
            def get_players_online_msg():
                players_online = self.online()
                if len(players_online) == 0:
                    return "No one online"
                else:
                    msg = "Players Online:\n"
                    for player in players_online:
                        msg += f"- {player}\n"
                    return msg

            response_dict = {
                "hello": "Hello World!",
                "!ip": self.get_ip(),
                "!online": get_players_online_msg()
            }
            if rcv_msg == "!help":
                resp = "Available Commands Are:\n"
                for key in response_dict.keys():
                    if key.startswith("!"):
                        resp += f"**{key}**\n"
            elif rcv_msg in response_dict.keys():
                resp = response_dict[rcv_msg]
            else:
                resp = None
            return resp

        if message.author.id == self.user.id:
            return

        if message.channel.id == response_channel_id:
            log.debug(f"Received: '{message.content}' from {message.author}")
            response = get_response(message.content.lower())
            if response is not None:
                await self.send_msg(response)


argparser = ArgumentParser()
argparser.add_argument("--log-level", type=str, default="DEBUG")
args = argparser.parse_args()

log.setLevel(args.log_level)
client = MCServerClient(member_cache_flags=member_cache, intents=intents,
                        activity=discord.Activity(type=discord.ActivityType.listening, name="!help"))
client.run(token)
