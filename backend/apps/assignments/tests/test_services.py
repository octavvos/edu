"""Mentor uy vazifalarini boshqarishi: taqsimlash, holat o'tishlari, baholash."""

from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from apps.accounts.tests.factories import PendingUserFactory, UserFactory
from apps.assignments import services
from apps.assignments.models import Homework, SubmissionStatus
from apps.assignments.tests.factories import HomeworkFactory, LessonFactory
from apps.core.exceptions import DomainError
from apps.courses import services as course_services
from apps.enrollment.selectors import get_enrollment
from apps.groups import services as group_services
from apps.groups.tests.factories import GroupFactory

pytestmark = pytest.mark.django_db


def _student_in_group_of(mentor, *, course=None):
    """Mentorning guruhiga qabul qilingan o'quvchi qaytaradi."""
    group = GroupFactory(mentor=mentor, **({"course": course} if course else {}))
    student = PendingUserFactory()
    group_services.approve_join_request(
        request_obj=group_services.create_join_request(student=student, group=group),
        mentor=mentor,
    )
    return student, group


def _submit(student, group, **homework_kwargs):
    homework = HomeworkFactory(lesson__module__course=group.course, group=group, **homework_kwargs)
    enrollment = get_enrollment(user=student, course=group.course)
    return services.submit_homework(
        user=student, enrollment=enrollment, homework=homework, text="Bajardim",
    )


# ---------------------------------------------------------------------------
# Mentorga taqsimlash
# ---------------------------------------------------------------------------

def test_submission_is_assigned_to_the_mentor_of_students_group():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)

    submission = _submit(student, group)

    assert submission.mentor_id == mentor.id
    assert submission.status == SubmissionStatus.SUBMITTED


def test_submission_requires_some_content():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    homework = HomeworkFactory(lesson__module__course=group.course)
    enrollment = get_enrollment(user=student, course=group.course)

    with pytest.raises(DomainError) as exc:
        services.submit_homework(user=student, enrollment=enrollment, homework=homework)
    assert exc.value.code == "empty_submission"


def test_late_submission_is_flagged():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)

    submission = _submit(student, group, deadline_at=timezone.now() - timedelta(days=1))

    assert submission.is_late is True


def test_submission_before_deadline_is_not_late():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)

    submission = _submit(student, group, deadline_at=timezone.now() + timedelta(days=1))

    assert submission.is_late is False


# ---------------------------------------------------------------------------
# Holat o'tishlari (H-03)
# ---------------------------------------------------------------------------

def test_mentor_can_move_submission_to_under_review():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    updated = services.change_submission_status(
        mentor=mentor, submission=submission, new_status=SubmissionStatus.UNDER_REVIEW,
    )
    assert updated.status == SubmissionStatus.UNDER_REVIEW


def test_accepted_submission_cannot_change_status():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)
    services.grade_submission(mentor=mentor, submission=submission, score=90)

    with pytest.raises(DomainError) as exc:
        services.change_submission_status(
            mentor=mentor, submission=submission, new_status=SubmissionStatus.UNDER_REVIEW,
        )
    assert exc.value.code == "invalid_transition"


def test_cannot_accept_without_grading():
    """'Qabul qilindi' holatiga faqat baho orqali o'tiladi."""
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    with pytest.raises(DomainError) as exc:
        services.change_submission_status(
            mentor=mentor, submission=submission, new_status=SubmissionStatus.ACCEPTED,
        )
    assert exc.value.code == "grade_required"


def test_other_mentor_cannot_review_submission():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    with pytest.raises(DomainError) as exc:
        services.change_submission_status(
            mentor=UserFactory(), submission=submission,
            new_status=SubmissionStatus.UNDER_REVIEW,
        )
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Baholash (H-04)
# ---------------------------------------------------------------------------

def test_grading_accepts_submission_and_stores_feedback():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    updated = services.grade_submission(
        mentor=mentor, submission=submission, score=85, feedback="Yaxshi ish",
    )

    assert updated.status == SubmissionStatus.ACCEPTED
    assert updated.grade.score == 85
    assert updated.grade.feedback == "Yaxshi ish"


def test_grading_with_needs_revision_sends_back():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    updated = services.grade_submission(
        mentor=mentor, submission=submission, score=40,
        feedback="Qayta ishlang", needs_revision=True,
    )

    assert updated.status == SubmissionStatus.NEEDS_REVISION
    assert updated.grade.score == 40


@pytest.mark.parametrize("score", [-1, 101])
def test_score_outside_zero_to_hundred_is_rejected(score):
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    with pytest.raises(DomainError) as exc:
        services.grade_submission(mentor=mentor, submission=submission, score=score)
    assert exc.value.code == "invalid_score"


def test_already_accepted_submission_cannot_be_regraded():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)
    services.grade_submission(mentor=mentor, submission=submission, score=90)

    with pytest.raises(DomainError) as exc:
        services.grade_submission(mentor=mentor, submission=submission, score=50)
    assert exc.value.code == "already_accepted"


def test_other_mentor_cannot_grade():
    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    with pytest.raises(DomainError) as exc:
        services.grade_submission(mentor=UserFactory(), submission=submission, score=90)
    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# Mentor navbati
# ---------------------------------------------------------------------------

def test_mentor_queue_shows_only_own_students_and_hides_accepted():
    from apps.assignments.selectors import get_mentor_queue

    mentor = UserFactory()
    other_mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    other_student, other_group = _student_in_group_of(other_mentor)

    mine = _submit(student, group)
    _submit(other_student, other_group)

    assert list(get_mentor_queue(mentor)) == [mine]

    services.grade_submission(mentor=mentor, submission=mine, score=100)
    assert list(get_mentor_queue(mentor)) == []


def test_mentor_queue_puts_late_submissions_first():
    from apps.assignments.selectors import get_mentor_queue

    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)

    _submit(student, group)  # o'z vaqtida
    late = _submit(student, group, deadline_at=timezone.now() - timedelta(days=2))

    assert get_mentor_queue(mentor).first() == late


# ---------------------------------------------------------------------------
# Vazifa jo'natish (mentor -> guruh)
# ---------------------------------------------------------------------------

def test_send_homework_creates_it_for_chosen_group():
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    lesson = LessonFactory(module__course=group.course)

    homework = services.send_homework(
        mentor=mentor, lesson=lesson, group=group,
        instructions={"uz": "PDF shaklida topshiring"}, max_score=50,
    )

    assert homework.lesson_id == lesson.id
    assert homework.group_id == group.id
    assert homework.max_score == 50


def test_send_homework_twice_to_same_group_updates_instead_of_duplicating():
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    lesson = LessonFactory(module__course=group.course)

    services.send_homework(mentor=mentor, lesson=lesson, group=group,
                           instructions={"uz": "V1"}, max_score=100)
    updated = services.send_homework(mentor=mentor, lesson=lesson, group=group,
                                     instructions={"uz": "V2"}, max_score=80)

    assert Homework.objects.filter(lesson=lesson, group=group).count() == 1
    assert updated.max_score == 80
    assert updated.instructions["uz"] == "V2"


def test_same_lesson_can_be_sent_to_several_groups_independently():
    """Bitta kursni bir necha guruh baham ko'radi — har biriga o'z muddati bilan."""
    mentor = UserFactory()
    _, group_a = _student_in_group_of(mentor)
    group_b = GroupFactory(mentor=mentor, course=group_a.course)
    lesson = LessonFactory(module__course=group_a.course)

    services.send_homework(mentor=mentor, lesson=lesson, group=group_a,
                           instructions={"uz": "A guruh"}, max_score=100)
    services.send_homework(mentor=mentor, lesson=lesson, group=group_b,
                           instructions={"uz": "B guruh"}, max_score=60)

    assert Homework.objects.filter(lesson=lesson).count() == 2
    assert Homework.objects.get(lesson=lesson, group=group_b).max_score == 60


def test_send_homework_rejected_for_unrelated_mentor():
    mentor = UserFactory()
    outsider = UserFactory()
    _, group = _student_in_group_of(mentor)
    lesson = LessonFactory(module__course=group.course)

    with pytest.raises(DomainError) as exc:
        services.send_homework(mentor=outsider, lesson=lesson, group=group, instructions={"uz": "V1"})
    assert exc.value.status_code == 403


def test_send_homework_rejected_for_another_mentors_group():
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    lesson = LessonFactory(module__course=group.course)
    other_group = GroupFactory(mentor=UserFactory(), course=group.course)

    with pytest.raises(DomainError) as exc:
        services.send_homework(mentor=mentor, lesson=lesson, group=other_group,
                               instructions={"uz": "V1"})
    assert exc.value.code == "not_your_group"


def test_send_homework_rejects_group_from_another_course():
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    lesson = LessonFactory(module__course=group.course)
    foreign_group = GroupFactory(mentor=mentor)  # boshqa kursning guruhi

    with pytest.raises(DomainError) as exc:
        services.send_homework(mentor=mentor, lesson=lesson, group=foreign_group,
                               instructions={"uz": "V1"})
    assert exc.value.code == "group_course_mismatch"


def test_send_homework_with_material_from_same_lesson():
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    lesson = LessonFactory(module__course=group.course)
    material = course_services.add_file_material(
        lesson=lesson, file=SimpleUploadedFile("slayd.pdf", b"%PDF-1.4"),
        title="Slaydlar", kind="presentation",
    )

    homework = services.send_homework(
        mentor=mentor, lesson=lesson, group=group,
        instructions={"uz": "Slaydni ko'rib chiqing"}, material=material,
    )

    assert homework.material_id == material.id


def test_send_homework_rejects_material_from_another_lesson():
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    lesson = LessonFactory(module__course=group.course)
    other_lesson = LessonFactory(module__course=group.course)
    material = course_services.add_file_material(
        lesson=other_lesson, file=SimpleUploadedFile("slayd.pdf", b"%PDF-1.4"),
        title="Slaydlar", kind="presentation",
    )

    with pytest.raises(DomainError) as exc:
        services.send_homework(mentor=mentor, lesson=lesson, group=group,
                               instructions={"uz": "V1"}, material=material)
    assert exc.value.code == "material_mismatch"


def test_send_homework_with_both_task_material_and_presentation():
    """Vazifa fayli va taqdimot bir-biridan mustaqil — ikkalasi ham birga jo'natilishi mumkin."""
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    lesson = LessonFactory(module__course=group.course)
    task_file = course_services.add_file_material(
        lesson=lesson, file=SimpleUploadedFile("vazifa.pdf", b"%PDF-1.4"),
        title="Vazifa fayli", kind="task",
    )
    presentation = course_services.add_file_material(
        lesson=lesson, file=SimpleUploadedFile("slayd.pdf", b"%PDF-1.4"),
        title="Slaydlar", kind="presentation",
    )

    homework = services.send_homework(
        mentor=mentor, lesson=lesson, group=group,
        instructions={"uz": "Vazifa va taqdimot"}, material=task_file, presentation=presentation,
    )

    assert homework.material_id == task_file.id
    assert homework.presentation_id == presentation.id


def test_send_homework_notifies_active_group_students(monkeypatch):
    """Vazifa jo'natilganda guruhning har bir faol o'quvchisiga in-app bildirishnoma tayyorlanadi."""
    from unittest.mock import Mock

    from apps.notifications.models import NotificationEvent

    delay_mock = Mock()
    monkeypatch.setattr("apps.notifications.tasks.dispatch_notification.delay", delay_mock)

    mentor = UserFactory()
    student_a, group = _student_in_group_of(mentor)
    student_b = PendingUserFactory()
    group_services.approve_join_request(
        request_obj=group_services.create_join_request(student=student_b, group=group), mentor=mentor,
    )
    lesson = LessonFactory(module__course=group.course)

    services.send_homework(mentor=mentor, lesson=lesson, group=group, instructions={"uz": "Bajaring"})

    assert delay_mock.call_count == 2
    notified_user_ids = {call.kwargs["user_id"] for call in delay_mock.call_args_list}
    assert notified_user_ids == {str(student_a.id), str(student_b.id)}
    for call in delay_mock.call_args_list:
        assert call.kwargs["event"] == NotificationEvent.HOMEWORK_ASSIGNED
        assert lesson.title["uz"] in call.kwargs["context"]["text"]


def test_send_homework_does_not_notify_removed_student(monkeypatch):
    from unittest.mock import Mock

    delay_mock = Mock()
    monkeypatch.setattr("apps.notifications.tasks.dispatch_notification.delay", delay_mock)

    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    group.memberships.filter(student=student).update(status="removed")
    lesson = LessonFactory(module__course=group.course)

    services.send_homework(mentor=mentor, lesson=lesson, group=group, instructions={"uz": "Bajaring"})

    delay_mock.assert_not_called()


def test_send_homework_rejects_presentation_from_another_lesson():
    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    lesson = LessonFactory(module__course=group.course)
    other_lesson = LessonFactory(module__course=group.course)
    presentation = course_services.add_file_material(
        lesson=other_lesson, file=SimpleUploadedFile("slayd.pdf", b"%PDF-1.4"),
        title="Slaydlar", kind="presentation",
    )

    with pytest.raises(DomainError) as exc:
        services.send_homework(mentor=mentor, lesson=lesson, group=group,
                               instructions={"uz": "V1"}, presentation=presentation)
    assert exc.value.code == "presentation_mismatch"


# ---------------------------------------------------------------------------
# O'quvchiga ko'rinadigan vazifalar ro'yxati
# ---------------------------------------------------------------------------

def test_get_my_assignments_shows_only_homework_sent_to_own_group():
    from apps.assignments.selectors import get_my_assignments

    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    other_group = GroupFactory(mentor=mentor, course=group.course)
    lesson = LessonFactory(module__course=group.course)

    mine = services.send_homework(mentor=mentor, lesson=lesson, group=group,
                                  instructions={"uz": "Mening guruhimga"})
    services.send_homework(mentor=mentor, lesson=LessonFactory(module__course=group.course),
                           group=other_group, instructions={"uz": "Boshqa guruhga"})

    rows = get_my_assignments(student)
    assert [r.id for r in rows] == [mine.id]
    assert rows[0]._my_submission is None


def test_get_my_assignments_includes_both_material_and_presentation():
    from apps.assignments.selectors import get_my_assignments

    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    lesson = LessonFactory(module__course=group.course)
    task_file = course_services.add_file_material(
        lesson=lesson, file=SimpleUploadedFile("vazifa.pdf", b"%PDF-1.4"),
        title="Vazifa fayli", kind="task",
    )
    presentation = course_services.add_file_material(
        lesson=lesson, file=SimpleUploadedFile("slayd.pdf", b"%PDF-1.4"),
        title="Slaydlar", kind="presentation",
    )
    services.send_homework(
        mentor=mentor, lesson=lesson, group=group,
        instructions={"uz": "Ikkalasi ham"}, material=task_file, presentation=presentation,
    )

    row = get_my_assignments(student)[0]
    assert row.material_id == task_file.id
    assert row.presentation_id == presentation.id


def test_get_my_assignments_attaches_own_submission():
    from apps.assignments.selectors import get_my_assignments

    mentor = UserFactory()
    student, group = _student_in_group_of(mentor)
    submission = _submit(student, group)

    rows = get_my_assignments(student)
    matching = [r for r in rows if r.id == submission.homework_id][0]
    assert matching._my_submission.id == submission.id


def test_get_my_assignments_empty_for_student_without_group():
    from apps.assignments.selectors import get_my_assignments

    mentor = UserFactory()
    _, group = _student_in_group_of(mentor)
    lesson = LessonFactory(module__course=group.course)
    services.send_homework(mentor=mentor, lesson=lesson, group=group, instructions={"uz": "Bajaring"})

    outsider = UserFactory()
    assert get_my_assignments(outsider) == []


# ---------------------------------------------------------------------------
# Topshiriq fayli validatsiyasi (zip/pdf, hajm)
# ---------------------------------------------------------------------------

def test_submission_serializer_rejects_disallowed_extension():
    from apps.assignments.api.serializers import SubmissionCreateSerializer

    upload = SimpleUploadedFile("hisobot.docx", b"fake", content_type="application/octet-stream")
    serializer = SubmissionCreateSerializer(data={"file": upload})

    assert not serializer.is_valid()
    assert "file" in serializer.errors


@pytest.mark.parametrize("filename", ["ish.zip", "hisobot.pdf"])
def test_submission_serializer_accepts_zip_and_pdf(filename):
    from apps.assignments.api.serializers import SubmissionCreateSerializer

    upload = SimpleUploadedFile(filename, b"fake content")
    serializer = SubmissionCreateSerializer(data={"file": upload})

    assert serializer.is_valid(), serializer.errors


def test_submission_serializer_rejects_oversized_file():
    from apps.assignments.api.serializers import SubmissionCreateSerializer
    from apps.assignments.constants import MAX_SUBMISSION_SIZE_BYTES

    oversized = SimpleUploadedFile("ish.zip", b"x" * (MAX_SUBMISSION_SIZE_BYTES + 1))
    serializer = SubmissionCreateSerializer(data={"file": oversized})

    assert not serializer.is_valid()
    assert "file" in serializer.errors
