"""
TZ 5.9: uz-lotin <-> uz-kiril transliteratsiyasi — qidiruvda ikkala
variant ham indekslanadi, shunda foydalanuvchi «дастурлаш» yoki
«dasturlash» yozsa ham kurs topiladi.
"""

_CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "ye", "ё": "yo",
    "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "x", "ц": "s", "ч": "ch", "ш": "sh", "щ": "sh", "ъ": "",
    "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya", "ў": "o'", "қ": "q",
    "ғ": "g'", "ҳ": "h",
}
_LAT_TO_CYR = {v: k for k, v in sorted(_CYR_TO_LAT.items(), key=lambda kv: -len(kv[1])) if v}
# Ko'p harfli birikmalarni birinchi almashtirish uchun uzunlik bo'yicha tartiblangan
_MULTI_CHAR_LAT = sorted((k for k in _LAT_TO_CYR if len(k) > 1), key=len, reverse=True)


def cyrillic_to_latin(text: str) -> str:
    result = []
    for ch in text:
        lower = ch.lower()
        mapped = _CYR_TO_LAT.get(lower, lower)
        if ch.isupper() and mapped:
            mapped = mapped[0].upper() + mapped[1:]
        result.append(mapped)
    return "".join(result)


def latin_to_cyrillic(text: str) -> str:
    lowered = text.lower()
    out = []
    i = 0
    while i < len(lowered):
        matched = False
        for chunk in _MULTI_CHAR_LAT:
            if lowered.startswith(chunk, i):
                out.append(_LAT_TO_CYR[chunk])
                i += len(chunk)
                matched = True
                break
        if not matched:
            out.append(_LAT_TO_CYR.get(lowered[i], lowered[i]))
            i += 1
    return "".join(out)


def is_cyrillic(text: str) -> bool:
    return any("а" <= ch.lower() <= "я" or ch.lower() in "ёў қғҳ" for ch in text)
