import asyncio, async_timeout, math
import discord

from discord.ext import commands
from agrobot.exceptions import VoiceError, YTDLError
from agrobot.model import AudioStream, AudioStreamQueue
from agrobot.source import YTDLSource

class AgrobotMusicState:

    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot, self._ctx = bot, ctx

        self.current = None
        self.voice = None
        self.timeout = False
        self.next = asyncio.Event()
        self.queue = AudioStreamQueue()

        self._loop = False
        self._volume = 0.5

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __bool__(self):
        return not self.timeout

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()

            if not self.loop:
                try:
                    async with async_timeout.timeout(180):
                        self.current = await self.queue.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    self.timeout = True
                    return

            self.current.source.volume = self._volume
            self.voice.play(self.current.source, after=self.play_next)

            await self.current.source.channel.send(embed=self.create_embed())
            await self.next.wait()

    def play_next(self, error=None):
        if error:
            raise VoiceError(error)
        self.next.set()

    def skip(self):
        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.queue.clear()
        if self.voice:
            await self.voice.disconnect()
            self.voice = None

    def create_embed(self):
        current = self.current
        info = self.current.content_info

        return (discord.Embed(
                title='Trenutno svira:',
                description=f'```css\n{info.title}\n```',
                color=discord.Color.blurple())
                .add_field(name='Trajanje', value=current.duration)
                .add_field(name='Zatražio', value=current.requester.mention)
                .add_field(name='Objavio', value=f'[{info.uploader}]({info.uploader_url})')
                .add_field(name='Link', value=f'[ovdje]({info.url})')
                .set_thumbnail(url=info.thumbnail))

class AgrobotMusic(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id, None)
        if not state:
            state = AgrobotMusicState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state
        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('Nemreš ovo koristit u DM-ovima.')
        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send(f'Eto greške: {error!s}')

    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context, channel: discord.VoiceChannel = None):
        dest = channel or ctx.author.voice.channel
        if ctx.voice_state.voice:
            await ctx.voice_state.voice.move_to(dest)
            return
        ctx.voice_state.voice = await dest.connect()

    @commands.command(name='leave', aliases=['l'])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        if not ctx.voice_state.voice:
            return await ctx.send('Nisam u kanalu, šta sad?')
        await ctx.voice_state.stop()
        del self.voice_states[ctx.guild.id]

    @commands.command(name='volume')
    async def _volume(self, ctx: commands.Context, volume: int):
        if not ctx.voice_state.is_playing:
            return await ctx.send('Trenutno ništa ne svira...')

        if 0 > volume > 100:
            return await ctx.send('Jel znaš ti šta su postotci?')

        ctx.voice_state.volume = volume / 100
        await ctx.send(f'Volumen je sad na {volume}%')

    @commands.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context):
        if not ctx.voice_state.is_playing:
            return await ctx.send('Trenutno ništa ne svira...')
        await ctx.send(embed=ctx.voice_state.create_embed())

    @commands.command(name='pause')
    @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx: commands.Context):
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
            ctx.voice_state.voice.pause()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='resume')
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
            ctx.voice_state.voice.resume()
            await ctx.message.add_reaction('⏯')

    @commands.command(name='stop')
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        ctx.voice_state.queue.clear()
        if ctx.voice_state.is_playing:
            ctx.voice_state.voice.stop()
            await ctx.message.add_reaction('⏹')

    @commands.command(name='skip')
    async def _skip(self, ctx: commands.Context):
        if not ctx.voice_state.is_playing:
            return await ctx.send('Trenutno ništa ne svira...')
        ctx.voice_state.skip()
        await ctx.message.add_reaction('⏭')

    @commands.command(name='queue', aliases=['q'])
    async def _queue(self, ctx: commands.Context, page: int = 1):
        if not (l := len(ctx.voice_state.queue)):
            return await ctx.send('Prazan red čekanja, lmao.')

        items_per_page = 10
        pages = math.ceil(l / items_per_page)
        start = (page - 1) * items_per_page
        end = start + items_per_page

        queue = ''
        for i, stream in enumerate(ctx.voice_state.queue[start:end], start=start):
            info = stream.content_info
            queue += f'`{i+1}.` [**{info.title}**]({info.url})\n'

        embed = (discord.Embed(description=f'**Red čekanja: {l}**\n\n{queue}')
                .set_footer(text=f'Gledaš stranicu {page}/{pages}'))
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        if not len(ctx.voice_state.queue):
            return await ctx.send('Prazan red čekanja, lmao.')
        ctx.voice_state.queue.shuffle()
        await ctx.message.add_reaction('✅')

    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int = 0):
        if not len(ctx.voice_state.queue):
            return await ctx.send('Prazan red čekanja, lmao.')
        ctx.voice_state.queue.remove(index - 1)
        await ctx.message.add_reaction('✅')

    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        if not ctx.voice_state.is_playing:
            return await ctx.send('Trenutno ništa ne svira...')
        ctx.voice_state.loop = not ctx.voice_state.loop
        await ctx.message.add_reaction('✅')

    @commands.command(name='play', aliases=['p'])
    async def _play(self, ctx: commands.Context, *, search: str):
        if not ctx.voice_state.voice:
            await ctx.invoke(self._join)
        async with ctx.typing():
            try:
                source = await YTDLSource.create(ctx, search, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send(str(e))
            else:
                stream = AudioStream(source)
                await ctx.voice_state.queue.put(stream)
                await ctx.send(f'Ide glazba: {stream!s}')

    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('Nisi u kanalu, šta sad?')
        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Već sam u kanalu.')
