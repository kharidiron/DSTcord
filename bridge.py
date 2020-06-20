#!/usr/bin/env python3

import asyncio
import re

import aiofiles
from discord.ext import commands
import watchgod
import yaml


description = '''
A DST to Discord Bridge.

Relies on some hackery using named pipes when starting the DST server.

I'll document that bit later.
'''


with open('vars.yml', 'r') as f:
    vars = yaml.load(f, Loader=yaml.FullLoader)


bot = commands.Bot(command_prefix=vars['prefix'])

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    channel = bot.get_channel(int(vars['channel_id']))
    await channel.send("DST Bridge is live!")
    await channel.send(f"Join the server '{vars['cluster_name']}'. Password is '{vars['cluster_password']}'.")

    await asyncio.gather(incoming_game_message())


@bot.command(description="Information on how to connect to the DST Server")
async def connect(ctx):
    await ctx.send(f"Server name is '{vars['cluster_name']}'. The password is '{vars['cluster_password']}'.")


@bot.listen('on_message')
async def incoming_discord_message(message):
    if message.author.id == bot.user.id:
        return

    if message.content.startswith(bot.command_prefix):
        """
        Watch for commands
        """
        await bot.process_commands(message)

    with open(vars['dst_pipe'], 'w') as pipe:
        pipe.write(f'TheNet:SystemMessage("[DC] <{message.author.display_name}> {message.content}")\n')


preamble_strip = re.compile("\[\d\d:\d\d:\d\d\]: \[(.*)\] (\(.*\) )?")
spoken_parse = re.compile("^(.*?): (.*)")


async def incoming_game_message():
    async with aiofiles.open(vars['dst_chatlog'], mode='r') as f:
        async for _ in watchgod.awatch(vars['dst_chatlog']):
            content = await f.readline()
            async for content in f:
                pass

            raw = content.rstrip()
            msg = preamble_strip.split(raw)

            try:
                if msg[1] =='Say':
                    spoken = spoken_parse.split(msg[3])
                    await(print_game_message(f"<{spoken[1]}> {spoken[2]}"))
                elif msg[1] == 'Join Announcement':
                    await(print_game_message(f"**{msg[3]} has joined**"))
                elif msg[1] == 'Leave Announcement':
                    await(print_game_message(f"**{msg[3]} has left**"))
                elif msg[1] in ['Death Announcement', 'Resurrect Announcement']:
                    await(print_game_message(f"**{msg[3]}**"))
            except Exception as e:
                print(f"! Exception occurred. Type: {type(e).__name__}")
                print(f"--- Bad line ---: {raw}")


async def print_game_message(message):
    channel = bot.get_channel(int(vars['channel_id']))

    await channel.send(message)


if __name__ == '__main__':
    bot.run(vars['token'], bot=True)
