from celery import shared_task


@shared_task
def reindex_course(course_id: str):
    """TZ 5.9: Course saqlangandan keyin search_vector'ni yangilaydi (post_save signal orqali chaqiriladi)."""
    from django.contrib.postgres.search import SearchVector

    from apps.catalog.transliteration import cyrillic_to_latin, latin_to_cyrillic
    from apps.core.models import get_i18n_value
    from apps.courses.models import Course

    course = Course.objects.filter(id=course_id).first()
    if not course:
        return

    title_uz = get_i18n_value(course, "title", "uz")
    title_ru = get_i18n_value(course, "title", "ru")
    translit_variants = " ".join(filter(None, [
        title_uz, latin_to_cyrillic(title_uz), cyrillic_to_latin(title_uz),
    ]))

    Course.objects.filter(id=course_id).update(
        title_plain=title_uz,
        search_vector=(
            SearchVector("title_plain", weight="A")
            + SearchVector("description_plain", weight="B")
        ),
    )
    # translit_variants alohida CharField'ga yozilishi mumkin — MVP uchun
    # title_plain orqali TrigramSimilarity bilan qamrab olinadi (selectors.py).
    return translit_variants
