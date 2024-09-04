import logging
import discord

from discord.ext import commands
from agrobot.cog import AgrobotMusic
from agrobot.config.env import (
    DISCORDAPI_BOT_TOKEN,
    BOT_COMMAND_PREFIX,
    BOT_DESCRIPTION,
    LOCALE
)

__version__ = 0, 2, 1

print(r'''
    _                ___      _    
   /_\  __ _ _ _ ___| _ ) ___| |_  
  / _ \/ _` | '_/ _ \ _ \/ _ \  _| 
 /_/ \_\__, |_| \___/___/\___/\__| 
       |___/
'''[1:])

agrobot = commands.Bot(
    command_prefix=commands.when_mentioned_or(BOT_COMMAND_PREFIX),
    description=BOT_DESCRIPTION,
    intents=discord.Intents(
        voice_states=True,
        messages=True,
        message_content=True,
        guilds=True
    ))

@agrobot.event
async def on_ready():
    print(f'\nVersion: {".".join(map(str, __version__))}')
    print(f'Locale: {LOCALE}')
    print(f'Logged in as:\n\t{agrobot.user.name}\n\t{agrobot.user.id}\n')
    await agrobot.add_cog(AgrobotMusic(agrobot))

agrobot.run(DISCORDAPI_BOT_TOKEN, log_level=logging.INFO)
