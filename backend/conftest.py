import pytest


@pytest.fixture(autouse=True)
def _enable_db_access_for_all_tests(db):
    """Har bir test uchun DB kirishini avtomatik yoqadi (pytest-django)."""
