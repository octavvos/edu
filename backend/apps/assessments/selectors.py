from dataclasses import dataclass, field

from apps.assessments.models import Attempt, AttemptStatus, Question, Quiz
from apps.core.models import resolve_i18n


def get_my_quizzes(user, lang: str = "uz") -> list[dict]:
    """O'quvchining o'z guruhiga mentor tanlab jo'natgan testlari (Testlarim) —
    kursga yozilgan bo'lishning o'zi yetarli emas, test aynan shu guruhga
    yuborilgan bo'lishi kerak (Homework'ning guruh bo'yicha ko'rinish patterni)."""
    from apps.groups.selectors import get_active_membership

    membership = get_active_membership(user)
    if not membership:
        return []

    quizzes = (
        Quiz.objects.filter(assignments__group=membership.group)
        .select_related("lesson__module__course")
        .prefetch_related("questions")
        .distinct()
        .order_by("lesson__module__order", "lesson__order")
    )

    results = []
    for quiz in quizzes:
        lesson = quiz.lesson
        attempts = list(Attempt.objects.filter(user=user, quiz=quiz).order_by("-started_at"))
        submitted = [a for a in attempts if a.status == AttemptStatus.SUBMITTED]
        best_score = max((a.score_percent for a in submitted if a.score_percent is not None), default=None)
        passed = any(a.passed for a in submitted)
        in_progress = next((a for a in attempts if a.status == AttemptStatus.IN_PROGRESS), None)

        results.append({
            "lesson_id": str(lesson.id),
            "title": resolve_i18n(lesson.title, lang),
            "module_title": resolve_i18n(lesson.module.title, lang),
            "course_title": resolve_i18n(lesson.module.course.title, lang),
            "question_count": quiz.questions.count(),
            "time_limit_seconds": quiz.time_limit_seconds,
            "max_attempts": quiz.max_attempts,
            "pass_percent": quiz.pass_percent,
            "attempt_count": len(attempts),
            "best_score": best_score,
            "passed": passed,
            "has_in_progress": in_progress is not None,
            "in_progress_attempt_id": str(in_progress.id) if in_progress else None,
        })
    return results


def get_best_attempt_score(*, enrollment, quiz_lesson_id) -> float | None:
    best = (
        Attempt.objects.filter(
            enrollment=enrollment, quiz__lesson_id=quiz_lesson_id, status=AttemptStatus.SUBMITTED,
        )
        .order_by("-score_percent")
        .first()
    )
    return best.score_percent if best else None


def get_attempt_count(*, user, quiz) -> int:
    return Attempt.objects.filter(user=user, quiz=quiz).count()


def get_latest_attempt(*, user, quiz):
    return Attempt.objects.filter(user=user, quiz=quiz).order_by("-started_at").first()


# ---------------------------------------------------------------------------
# Mentor: test natijalari tahlili — guruh bo'yicha reyting va o'quvchi tafsiloti
# ---------------------------------------------------------------------------


def _time_taken_seconds(attempt: Attempt) -> int | None:
    if not attempt.submitted_at:
        return None
    return round((attempt.submitted_at - attempt.started_at).total_seconds())


def _best_attempts_by_quiz(attempts: list[Attempt]) -> dict[str, Attempt]:
    """Har bir test bo'yicha eng yuqori ballli topshirilgan urinish."""
    best: dict[str, Attempt] = {}
    for attempt in attempts:
        if attempt.status != AttemptStatus.SUBMITTED:
            continue
        current = best.get(attempt.quiz_id)
        if current is None or (attempt.score_percent or 0) > (current.score_percent or 0):
            best[attempt.quiz_id] = attempt
    return best


@dataclass
class GroupQuizSummary:
    group_id: str
    group_name: str
    course_title: str
    tests_sent: int
    student_count: int
    avg_score: float | None
    completion_percent: float


def get_groups_with_quiz_results(mentor, lang: str = "uz") -> list[GroupQuizSummary]:
    """Mentorga tegishli, kamida bitta test jo'natilgan guruhlar ro'yxati —
    har biri uchun umumiy o'zlashtirish ko'rsatkichi bilan."""
    from apps.groups.models import Group, GroupMembership, MembershipStatus

    groups = (
        Group.objects.filter(mentor=mentor, quiz_assignments__isnull=False)
        .distinct()
        .select_related("course")
        .order_by("name")
    )

    rows = []
    for group in groups:
        quiz_ids = list(group.quiz_assignments.values_list("quiz_id", flat=True))
        student_ids = list(
            GroupMembership.objects.filter(group=group, status=MembershipStatus.ACTIVE)
            .values_list("student_id", flat=True),
        )
        attempts = list(
            Attempt.objects.filter(
                quiz_id__in=quiz_ids, user_id__in=student_ids, status=AttemptStatus.SUBMITTED,
            ),
        )
        best_per_pair: dict[tuple, Attempt] = {}
        for attempt in attempts:
            key = (attempt.user_id, attempt.quiz_id)
            current = best_per_pair.get(key)
            if current is None or (attempt.score_percent or 0) > (current.score_percent or 0):
                best_per_pair[key] = attempt

        avg_score = (
            round(sum(a.score_percent or 0 for a in best_per_pair.values()) / len(best_per_pair), 1)
            if best_per_pair
            else None
        )
        possible_pairs = len(quiz_ids) * len(student_ids)
        completion_percent = round(len(best_per_pair) / possible_pairs * 100, 1) if possible_pairs else 0.0

        rows.append(GroupQuizSummary(
            group_id=str(group.id),
            group_name=group.name,
            course_title=resolve_i18n(group.course.title, lang) if group.course_id else "",
            tests_sent=len(quiz_ids),
            student_count=len(student_ids),
            avg_score=avg_score,
            completion_percent=completion_percent,
        ))
    return rows


@dataclass
class QuizLeaderboardRow:
    rank: int
    student_id: str
    display_name: str
    username: str
    tests_assigned: int
    tests_solved: int
    avg_score: float | None
    total_time_seconds: int
    last_activity: str | None


def get_group_quiz_leaderboard(group) -> list[QuizLeaderboardRow]:
    """Guruhga jo'natilgan testlar bo'yicha o'quvchilar reytingi — yuqori
    o'rtacha ball tepada (Homework leaderboard patterniga o'xshash)."""
    from apps.groups.models import GroupMembership, MembershipStatus

    quiz_ids = list(group.quiz_assignments.values_list("quiz_id", flat=True))
    memberships = (
        GroupMembership.objects.filter(group=group, status=MembershipStatus.ACTIVE)
        .select_related("student")
    )
    student_ids = [m.student_id for m in memberships]
    attempts_by_student: dict = {}
    if quiz_ids and student_ids:
        for attempt in Attempt.objects.filter(quiz_id__in=quiz_ids, user_id__in=student_ids):
            attempts_by_student.setdefault(attempt.user_id, []).append(attempt)

    rows = []
    for membership in memberships:
        student = membership.student
        student_attempts = attempts_by_student.get(student.id, [])
        best_by_quiz = _best_attempts_by_quiz(student_attempts)
        tests_solved = len(best_by_quiz)
        avg_score = (
            round(sum(a.score_percent or 0 for a in best_by_quiz.values()) / tests_solved, 1)
            if tests_solved
            else None
        )
        total_time = sum(
            (_time_taken_seconds(a) or 0) for a in best_by_quiz.values()
        )
        submitted_dates = [a.submitted_at for a in student_attempts if a.submitted_at]
        last_activity = max(submitted_dates) if submitted_dates else None

        rows.append(QuizLeaderboardRow(
            rank=0,
            student_id=str(student.id),
            display_name=student.display_name,
            username=student.username,
            tests_assigned=len(quiz_ids),
            tests_solved=tests_solved,
            avg_score=avg_score,
            total_time_seconds=total_time,
            last_activity=last_activity.isoformat() if last_activity else None,
        ))

    rows.sort(key=lambda r: (-(r.avg_score if r.avg_score is not None else -1), -r.tests_solved, r.display_name.lower()))
    for index, row in enumerate(rows, start=1):
        row.rank = index
    return rows


@dataclass
class StudentQuizResultRow:
    lesson_id: str
    quiz_title: str
    module_title: str
    attempt_id: str | None
    status: str
    score_percent: float | None
    passed: bool | None
    time_taken_seconds: int | None
    submitted_at: str | None
    attempt_count: int


def get_student_quiz_results(group, student, lang: str = "uz") -> list[StudentQuizResultRow]:
    """Bitta o'quvchining shu guruhga jo'natilgan har bir testdagi natijasi."""
    quizzes = (
        Quiz.objects.filter(assignments__group=group)
        .select_related("lesson__module")
        .distinct()
        .order_by("lesson__module__order", "lesson__order")
    )

    rows = []
    for quiz in quizzes:
        attempts = list(Attempt.objects.filter(quiz=quiz, user=student).order_by("-started_at"))
        submitted = [a for a in attempts if a.status == AttemptStatus.SUBMITTED]
        best = max(submitted, key=lambda a: a.score_percent or 0, default=None)

        if best:
            row_status = "passed" if best.passed else "failed"
        else:
            row_status = "not_started"

        rows.append(StudentQuizResultRow(
            lesson_id=str(quiz.lesson_id),
            quiz_title=resolve_i18n(quiz.lesson.title, lang),
            module_title=resolve_i18n(quiz.lesson.module.title, lang),
            attempt_id=str(best.id) if best else None,
            status=row_status,
            score_percent=best.score_percent if best else None,
            passed=best.passed if best else None,
            time_taken_seconds=_time_taken_seconds(best) if best else None,
            submitted_at=best.submitted_at.isoformat() if best and best.submitted_at else None,
            attempt_count=len(attempts),
        ))
    return rows


@dataclass
class AnswerBreakdownRow:
    question_id: str
    question_text: str
    question_type: str
    points: int
    selected_choice_ids: list = field(default_factory=list)
    selected_texts: list = field(default_factory=list)
    correct_choice_ids: list = field(default_factory=list)
    correct_texts: list = field(default_factory=list)
    text_answer: str = ""
    is_correct: bool | None = None
    points_awarded: float = 0


@dataclass
class AttemptDetail:
    attempt_id: str
    quiz_title: str
    student_display_name: str
    score_percent: float | None
    passed: bool | None
    started_at: str
    submitted_at: str | None
    time_taken_seconds: int | None
    answers: list[AnswerBreakdownRow]


def get_attempt_detail(attempt: Attempt, lang: str = "uz") -> AttemptDetail:
    """Mentor uchun — o'quvchi har bir savolga nima belgilagani va bu to'g'ri
    bo'lganmi, to'g'ri javob bilan solishtirib ko'rsatish uchun."""
    questions = {
        str(q.id): q
        for q in Question.objects.filter(id__in=attempt.question_ids).prefetch_related("choices")
    }
    answers_by_question = {str(a.question_id): a for a in attempt.answers.all()}

    rows = []
    for question_id in attempt.question_ids:
        question = questions.get(question_id)
        if not question:
            continue
        answer = answers_by_question.get(question_id)
        choices = list(question.choices.all())
        choice_map = {str(c.id): c for c in choices}
        selected_ids = answer.selected_choice_ids if answer else []

        rows.append(AnswerBreakdownRow(
            question_id=question_id,
            question_text=resolve_i18n(question.text, lang),
            question_type=question.type,
            points=question.points,
            selected_choice_ids=selected_ids,
            selected_texts=[
                resolve_i18n(choice_map[cid].text, lang) for cid in selected_ids if cid in choice_map
            ],
            correct_choice_ids=[str(c.id) for c in choices if c.is_correct],
            correct_texts=[resolve_i18n(c.text, lang) for c in choices if c.is_correct],
            text_answer=answer.text_answer if answer else "",
            is_correct=answer.is_correct if answer else None,
            points_awarded=answer.points_awarded if answer else 0,
        ))

    return AttemptDetail(
        attempt_id=str(attempt.id),
        quiz_title=resolve_i18n(attempt.quiz.lesson.title, lang),
        student_display_name=attempt.user.display_name,
        score_percent=attempt.score_percent,
        passed=attempt.passed,
        started_at=attempt.started_at.isoformat(),
        submitted_at=attempt.submitted_at.isoformat() if attempt.submitted_at else None,
        time_taken_seconds=_time_taken_seconds(attempt),
        answers=rows,
    )
