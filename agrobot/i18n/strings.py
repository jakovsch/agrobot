from importlib import import_module
from agrobot.config.env import LOCALE

@type.__call__
class Strings:

    i18n_map = {}

    def __init__(self):
        module = import_module(f'.locales.{LOCALE}', package=__package__)
        type(self).i18n_map = getattr(module, LOCALE, {})

    def __getattribute__(self, name):
        try:
            return type(self).i18n_map[name]
        except KeyError:
            return f'string.{name}'
