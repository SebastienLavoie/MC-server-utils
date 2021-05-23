#!/usr/bin/env python3

import discord

import logging
import re
from sys import stdout
from configparser import ConfigParser
from pathlib import Path
from subprocess import run, PIPE

num_players = 3
response_channel = "server-evenements"

file_name = Path(__file__).stem
log = logging.getLogger(file_name)

handler = logging.StreamHandler(stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

log.addHandler(handler)
log.setLevel(logging.DEBUG)

config = ConfigParser()
config.read(Path.home().joinpath(".discord-creds.conf"))

token = config['default']["token"]
server_log = Path.home().joinpath("minecraft", "create-mod", "server.log")

client = discord.Client()


@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == "MC Server":
            break

    log.info(f"{client.user} has connected to guild {guild.name} with id {guild.id}")


@client.event
async def on_message(message):
    def online() -> dict:
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
            ip = run("dig +short myip.opendns.com @resolver1.opendns.com", shell=True, stdout=PIPE, universal_newlines=True)
            msg = ip.stdout
            log.info(f"Sending: {msg}")
            await message.channel.send(msg)
        elif message.content.lower() == "!online":
            players = online()
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

client.run(token)
