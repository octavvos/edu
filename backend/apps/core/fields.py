"""Umumiy DRF serializer maydonlari."""

from rest_framework import serializers

from apps.core.models import get_i18n_value


class I18nCharField(serializers.Field):
    """
    D-04 i18n JSONB maydonini ({"uz": "...", "ru": "..."}) klientga TAYYOR
    satr sifatida beradi.

    Xom lug'atni yuborish klientni til tanlash logikasini takrorlashga majbur
    qiladi va React'da obyektni render qilishga urinib xatolikka olib keladi.
    Til `request.query_params["lang"]` yoki foydalanuvchi profilidan olinadi.
    """

    def __init__(self, source_field: str | None = None, **kwargs):
        kwargs.setdefault("read_only", True)
        self._source_field = source_field
        super().__init__(**kwargs)

    def get_attribute(self, instance):
        # Butun obyektni olamiz — qiymatni to_representation'da tilga qarab ochamiz
        return instance

    def to_representation(self, instance) -> str:
        field_name = self._source_field or self.field_name
        return get_i18n_value(instance, field_name, self._language())

    def _language(self) -> str:
        request = self.context.get("request")
        if not request:
            return "uz"
        lang = request.query_params.get("lang") if hasattr(request, "query_params") else None
        if lang:
            return lang
        user = getattr(request, "user", None)
        return getattr(user, "language", None) or "uz"
