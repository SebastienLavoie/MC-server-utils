#!/usr/bin/env python3

import discord

import logging
import re
from configparser import ConfigParser
from pathlib import Path
from subprocess import run, PIPE

log = logging.getLogger(__file__)
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

    print(f"{client.user} has connected to guild {guild.name} with id {guild.id}")


@client.event
async def on_message(message):
    def online() -> dict:
        players = dict()
        with open(server_log, "r") as fp:
            for line in reversed(fp.readlines()):
                patt = re.match(r"\[.*] \[Server thread/INFO] \[minecraft/DedicatedServer]: (.*) (.*) the game", line)
                if patt is not None:
                    if patt.group(1) not in players:
                        if patt.group(2) == "joined":
                            players[patt.group(1)] = True
                        else:
                            players[patt.group(1)] = False
                if len(players) == 2:
                    break
        return players

    if message.channel.name == "server-evenements":
        if message.content.lower() == "hello":
            await message.channel.send("Hello World!")
        elif message.content.lower() == "!ip":
            ip = run("dig +short myip.opendns.com @resolver1.opendns.com", shell=True, stdout=PIPE, universal_newlines=True)
            await message.channel.send(ip.stdout)
        elif message.content.lower() == "!online":
            players = online()
            if len(players) == 0:
                await message.channel.send("No one online")
            else:
                msg = str()
                for player, online in players.items():
                    if online is True:
                        msg += f"{player}\n"
                await message.channel.send(msg)

client.run(token)