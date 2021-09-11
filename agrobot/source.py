import asyncio, functools, types
import discord, youtube_dl

from discord.ext import commands
from agrobot.config.settings import ytdl_settings, ffmpeg_settings
from agrobot.exceptions import YTDLError

youtube_dl.utils.bug_reports_message = lambda: ''

class YTDLSource(discord.PCMVolumeTransformer):

    _handler = youtube_dl.YoutubeDL(ytdl_settings)
    _handler.cache.remove()

    def __init__(
        self,
        ctx: commands.Context,
        source: discord.FFmpegPCMAudio,
        content_info: dict,
        volume: float = 0.5
    ):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.content_info = types.SimpleNamespace(**content_info)

    @classmethod
    async def create(
        cls,
        ctx: commands.Context,
        url: str,
        loop: asyncio.BaseEventLoop = None,
        _process=False
    ):
        loop = loop or asyncio.get_event_loop()

        extractor = functools.partial(
            cls._handler.extract_info, url, download=False, process=_process
        )
        data = await loop.run_in_executor(None, extractor)

        if data is None:
            raise YTDLError(f'Error while fetching "{url}" :/')

        if 'entries' in data:
            if not any(data['entries']):
                raise YTDLError(f'Nothing found matching "{url}" :/')
            data = functools.reduce(lambda i, j: i or j, data['entries'])

        if not _process:
            return await cls.create(ctx, data['webpage_url'], loop, _process=True)

        return cls(ctx, discord.FFmpegPCMAudio(data['url'], **ffmpeg_settings), data)
