#!/usr/bin/env python3

import discord
import pyinotify

import logging
from configparser import ConfigParser
from pathlib import Path
from subprocess import run, PIPE

log = logging.getLogger(__file__)
config = ConfigParser()
config.read(Path.home().joinpath(".discord-creds.conf"))

token = config['default']["token"]

client = discord.Client()


@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == "MC Server":
            break

    print(f"{client.user} has connected to guild {guild.name} with id {guild.id}")


@client.event
async def on_message(message):
    if message.channel.name == "server-evenements":
        if message.content.lower() == "hello":
            await message.channel.send("Hello World!")
        elif message.content.lower() == "!ip":
            ip = run("dig +short myip.opendns.com @resolver1.opendns.com", shell=True, stdout=PIPE, universal_newlines=True)
            await message.channel.send(ip.stdout)


client.run(token)