from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Q

from apps.catalog.models import Category, Review, ReviewStatus
from apps.catalog.transliteration import cyrillic_to_latin, is_cyrillic, latin_to_cyrillic


def get_category_tree():
    """K-01: 2 darajali kategoriya daraxti."""
    categories = list(Category.objects.select_related("parent").order_by("order"))
    by_parent: dict = {}
    for cat in categories:
        by_parent.setdefault(cat.parent_id, []).append(cat)
    return by_parent.get(None, []), by_parent


def search_courses(*, query: str = "", category_slug: str = "", price: str = "", level: str = "",
                    language: str = "", min_rating: float | None = None, has_certificate: bool | None = None,
                    ordering: str = "popular"):
    """K-02/K-03/K-04: filtrlar, saralash, typo-tolerant transliteratsion qidiruv."""
    from apps.courses.models import Course, StatusChoices

    qs = Course.objects.filter(status=StatusChoices.PUBLISHED).select_related("category")

    if query:
        variants = {query}
        variants.add(latin_to_cyrillic(query) if not is_cyrillic(query) else cyrillic_to_latin(query))
        search_q = Q()
        for variant in variants:
            search_q |= Q(search_vector=variant) | Q(title__icontains=variant)
        qs = qs.filter(search_q).annotate(
            similarity=TrigramSimilarity("title_plain", query),
        ).filter(Q(similarity__gt=0.3) | search_q)

    if category_slug:
        qs = qs.filter(category__slug=category_slug)
    if price == "free":
        qs = qs.filter(price=0)
    elif price == "paid":
        qs = qs.filter(price__gt=0)
    if level:
        qs = qs.filter(level=level)
    if language:
        qs = qs.filter(language=language)
    if min_rating:
        qs = qs.filter(rating_avg__gte=min_rating)
    if has_certificate is not None:
        qs = qs.filter(issues_certificate=has_certificate)

    ordering_map = {
        "popular": "-enrollment_count",
        "new": "-published_at",
        "price_asc": "price",
        "price_desc": "-price",
        "rating": "-rating_avg",
    }
    return qs.order_by(ordering_map.get(ordering, "-enrollment_count"))


def get_recommendations(course) -> dict:
    """K-05: qoidaga asoslangan tavsiyalar."""
    from apps.courses.models import Course, StatusChoices

    same_category = Course.objects.filter(
        status=StatusChoices.PUBLISHED, category=course.category,
    ).exclude(id=course.id).order_by("-enrollment_count")[:8]

    bestsellers = Course.objects.filter(status=StatusChoices.PUBLISHED).order_by("-enrollment_count")[:8]
    newest = Course.objects.filter(status=StatusChoices.PUBLISHED).order_by("-published_at")[:8]

    return {
        "also_bought": list(same_category.values("id", "slug", "title", "price")),
        "bestsellers": list(bestsellers.values("id", "slug", "title", "price")),
        "new": list(newest.values("id", "slug", "title", "price")),
    }


def get_course_reviews(course):
    return Review.objects.filter(course=course, status=ReviewStatus.PUBLISHED).select_related("user")
