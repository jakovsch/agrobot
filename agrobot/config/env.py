import os, dotenv, pathlib

dotenv.load_dotenv(dotenv_path=pathlib.Path('.env'))

DISCORDAPI_BOT_TOKEN = os.getenv('DISCORDAPI_BOT_TOKEN', '')
BOT_COMMAND_PREFIX = os.getenv('BOT_COMMAND_PREFIX', '!')
BOT_DESCRIPTION = os.getenv('BOT_DESCRIPTION', '<todo>')
