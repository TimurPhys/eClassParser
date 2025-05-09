from .en import translations as en_translations
from .ru import translations as ru_translations
from .lv import translations as lv_translations

# Словарь всех переводов для всех языков
translations = {
    'en': en_translations,
    'ru': ru_translations,
    'lv': lv_translations,
}

def get_translation(key: str, lang: str = 'en', **kwargs) -> str:
    """Получить перевод по ключу для указанного языка"""
    # Если запрошенный язык не найден, пробуем английский как fallback
    # Если ключ не найден, возвращаем сам ключ (чтобы было видно, что перевод отсутствует)
    text = translations.get(lang, {}).get(key, translations['en'].get(key, key))
    return text.format(**kwargs) if kwargs else text