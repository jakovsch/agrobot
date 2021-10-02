import logging

from discord.ext import commands
from agrobot.cog import AgrobotMusic
from agrobot.config.env import (
    DISCORDAPI_BOT_TOKEN,
    BOT_COMMAND_PREFIX,
    BOT_DESCRIPTION,
    LOCALE
)

__version__ = 0, 1, 0

print(r'''
    _                ___      _    
   /_\  __ _ _ _ ___| _ ) ___| |_  
  / _ \/ _` | '_/ _ \ _ \/ _ \  _| 
 /_/ \_\__, |_| \___/___/\___/\__| 
       |___/
''')

logging.basicConfig(level=logging.INFO)

agrobot = commands.Bot(BOT_COMMAND_PREFIX, description=BOT_DESCRIPTION)
agrobot.add_cog(AgrobotMusic(agrobot))

@agrobot.event
async def on_ready():
    print(f'\nVersion: {".".join(map(str, __version__))}')
    print(f'Locale: {LOCALE}')
    print(f'Logged in as:\n\t{agrobot.user.name}\n\t{agrobot.user.id}\n')

agrobot.run(DISCORDAPI_BOT_TOKEN)
