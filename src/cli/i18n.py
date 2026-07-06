import gettext
import os

def setup_i18n(language: str):
    locales_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'locales')
    try:
        translation = gettext.translation('messages', localedir=locales_dir, languages=[language])
        translation.install()
        return translation.gettext
    except FileNotFoundError:
        return gettext.gettext
