#!/usr/bin/env python3

import discord
from configparser import ConfigParser
from pathlib import Path

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
    if message.content.lower() == "hello":
        message.channel.send("Hello World!")


client.run(token)