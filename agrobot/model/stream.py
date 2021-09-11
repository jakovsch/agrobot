
class AudioStream:

    __slots__ = 'source'

    def __init__(self, source):
        self.source = source

    def __str__(self):
        return f'**{self.content_info.title}** || **{self.content_info.uploader}**'

    @property
    def requester(self):
        return self.source.requester

    @property
    def content_info(self):
        return self.source.content_info

    @property
    def duration(self):
        d = int(self.content_info.duration)
        m, s = divmod(d, 60)
        h, m = divmod(m, 60)

        return f'{h:d}:{m:02d}:{s:02d}'
