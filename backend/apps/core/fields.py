"""Umumiy DRF serializer maydonlari."""

from rest_framework import serializers

from apps.core.models import resolve_i18n


class I18nCharField(serializers.Field):
    """
    D-04 i18n JSONB maydonini ({"uz": "...", "ru": "..."}) klientga TAYYOR
    satr sifatida beradi.

    Xom lug'atni yuborish klientni til tanlash logikasini takrorlashga majbur
    qiladi va React'da obyektni render qilishga urinib xatolikka olib keladi.

    DRF'ning standart `source` yo'li ishlaydi, shu jumladan ichma-ich:
        title = I18nCharField()
        lesson_title = I18nCharField(source="homework.lesson.title")

    Til `?lang=` so'rov parametridan yoki foydalanuvchi profilidan olinadi.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault("read_only", True)
        super().__init__(**kwargs)

    def to_representation(self, value) -> str:
        # `value` — i18n lug'ati (DRF source bo'yicha olib bergan)
        return resolve_i18n(value, self._language())

    def _language(self) -> str:
        request = self.context.get("request")
        if not request:
            return "uz"
        lang = getattr(request, "query_params", {}).get("lang") if request else None
        if lang:
            return lang
        return getattr(getattr(request, "user", None), "language", None) or "uz"
