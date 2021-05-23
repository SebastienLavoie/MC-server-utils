#!/usr/bin/env python3

import discord

import logging
import re
from configparser import ConfigParser
from pathlib import Path
from subprocess import run, PIPE

num_players = 3
response_channel = "server-evenements"

log = logging.getLogger(__file__)
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

    print(f"{client.user} has connected to guild {guild.name} with id {guild.id}")


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

    def send_message(message_obj, message):
        log.info(f"Sending {message}")
        await message_obj.channel.send(message)

    if message.channel.name == response_channel:
        log.debug(f"Received {message.content} from {message.author}")
        if message.content.lower() == "hello":
            send_message(message, "Hello World!")
        elif message.content.lower() == "!help":
            send_message(message, "Available commands: !ip, !online")
        elif message.content.lower() == "!ip":
            ip = run("dig +short myip.opendns.com @resolver1.opendns.com", shell=True, stdout=PIPE, universal_newlines=True)
            send_message(message, ip.stdout)
        elif message.content.lower() == "!online":
            players = online()
            if len(players) == 0:
                send_message(message, "No one online")
            else:
                msg = str()
                for player, online in players.items():
                    if online is True:
                        msg += f"{player}\n"
                msg = "No one online" if len(msg) == 0 else msg
                send_message(message, msg)

client.run(token)
