"""
"Dasturlash" kursidagi har bir mavzu uchun 10 savoldan, 15 daqiqa vaqt
chegarali test (quiz) va har bo'lim uchun yakuniy test (30/50 savol) yaratadi.

    python manage.py seed_course_quizzes

Har bir test alohida "Test: <mavzu>" nomli yangi quiz-turdagi darsga
biriktiriladi (mavjud matnli darslar o'zgarishsiz qoladi). Idempotent:
agar tegishli test darsi va savollari allaqachon mavjud bo'lsa, qayta
yaratilmaydi.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.assessments.models import Choice, Question, Quiz
from apps.assessments.seed_data import (
    database_quiz,
    deploy_quiz,
    django_quiz,
    python_quiz,
    scratch_quiz,
)
from apps.courses import services as course_services
from apps.courses.models import Course, LessonType

MODULES = [scratch_quiz, deploy_quiz, database_quiz, python_quiz, django_quiz]

QUIZ_DEFAULTS = {
    "max_attempts": 2,
    "pass_percent": 60,
}


class Command(BaseCommand):
    help = "'Dasturlash' kursiga mavzu va yakuniy testlarni (savollar bilan) urug'lantiradi"

    def handle(self, *args, **options):
        try:
            course = Course.objects.prefetch_related("modules__lessons").get(slug="dasturlash")
        except Course.DoesNotExist as exc:
            raise CommandError("'dasturlash' kursi topilmadi — avval seed_curriculum ishga tushiring") from exc

        created_quizzes = 0
        skipped_quizzes = 0

        with transaction.atomic():
            for mod in MODULES:
                module = course.modules.filter(title__uz=mod.MODULE_TITLE).first()
                if module is None:
                    self.stderr.write(self.style.WARNING(f"Modul topilmadi: {mod.MODULE_TITLE}"))
                    continue

                lessons_by_title = {lesson.title.get("uz"): lesson for lesson in module.lessons.all()}

                for lesson_title, questions in mod.QUESTIONS.items():
                    content_lesson = lessons_by_title.get(lesson_title)
                    if content_lesson is None:
                        self.stderr.write(self.style.WARNING(f"Dars topilmadi: {lesson_title}"))
                        continue
                    made = self._seed_quiz(
                        module=module,
                        quiz_title=f"Test: {lesson_title}",
                        time_limit_seconds=900,
                        questions=questions,
                    )
                    created_quizzes += int(made)
                    skipped_quizzes += int(not made)

                final = mod.FINAL
                made = self._seed_quiz(
                    module=module,
                    quiz_title=final["quiz_title"],
                    time_limit_seconds=final["time_limit_seconds"],
                    questions=final["questions"],
                )
                created_quizzes += int(made)
                skipped_quizzes += int(not made)

        self.stdout.write(self.style.SUCCESS(
            f"Tayyor: {created_quizzes} ta test yaratildi, {skipped_quizzes} ta allaqachon mavjud edi.",
        ))

    def _seed_quiz(self, *, module, quiz_title, time_limit_seconds, questions) -> bool:
        """True — yangi test yaratildi, False — allaqachon mavjud bo'lgani uchun o'tkazib yuborildi."""
        lesson = module.lessons.filter(type=LessonType.QUIZ, title__uz=quiz_title).first()
        if lesson is None:
            lesson = course_services.add_lesson(
                module=module, type=LessonType.QUIZ, title={"uz": quiz_title},
            )

        quiz, _ = Quiz.objects.get_or_create(
            lesson=lesson,
            defaults={"time_limit_seconds": time_limit_seconds, **QUIZ_DEFAULTS},
        )

        if quiz.questions.exists():
            return False

        for order, q in enumerate(questions, start=1):
            question = Question.objects.create(
                quiz=quiz,
                type="single_choice",
                text={"uz": q["text"]},
                points=1,
                order=order,
            )
            for choice_order, choice_text in enumerate(q["choices"], start=1):
                Choice.objects.create(
                    question=question,
                    text={"uz": choice_text},
                    is_correct=(choice_order - 1 == q["correct"]),
                    order=choice_order,
                )
        return True
