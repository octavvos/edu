from apps.communication.models import Comment, CommentStatus, HelpfulVote
from apps.core.exceptions import DomainError


def post_comment(*, user, lesson, text: str, is_question: bool = False, parent=None) -> Comment:
    return Comment.objects.create(
        lesson=lesson, user=user, text=text, is_question=is_question, parent=parent,
    )


def moderate_comment(*, actor, comment: Comment, approve: bool) -> Comment:
    comment.status = CommentStatus.PUBLISHED if approve else CommentStatus.HIDDEN
    comment.save(update_fields=["status"])

    from apps.audit.services import log_action

    log_action(actor=actor, action="comment.moderate", obj=comment, after={"status": comment.status})
    return comment


def vote_helpful(*, user, comment: Comment) -> Comment:
    _, created = HelpfulVote.objects.get_or_create(comment=comment, user=user)
    if not created:
        raise DomainError("Siz allaqachon ovoz bergansiz", code="already_voted")
    comment.helpful_count = comment.votes.count()
    comment.save(update_fields=["helpful_count"])
    return comment
