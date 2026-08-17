from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.communication import services
from apps.communication.api.serializers import CommentCreateSerializer, CommentSerializer
from apps.communication.models import Comment, CommentStatus
from apps.core.exceptions import DomainError


class LessonCommentsView(APIView):
    """N-01: dars ostida izohlar va Q&A."""

    def get_permissions(self):
        if self.request.method == "POST":
            from rest_framework.permissions import IsAuthenticated

            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, lesson_id):
        comments = Comment.objects.filter(
            lesson_id=lesson_id, parent__isnull=True, status=CommentStatus.PUBLISHED,
        ).select_related("user").prefetch_related("replies")
        return Response(CommentSerializer(comments, many=True).data)

    def post(self, request, lesson_id):
        from apps.courses.models import Lesson

        lesson = Lesson.objects.filter(id=lesson_id).first()
        if not lesson:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = CommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        parent = Comment.objects.filter(id=data["parent"]).first() if data["parent"] else None
        comment = services.post_comment(
            user=request.user, lesson=lesson, text=data["text"], is_question=data["is_question"], parent=parent,
        )
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentVoteHelpfulView(APIView):
    def post(self, request, comment_id):
        comment = Comment.objects.filter(id=comment_id).first()
        if not comment:
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            comment = services.vote_helpful(user=request.user, comment=comment)
        except DomainError as exc:
            return Response({"detail": exc.detail}, status=exc.status_code)
        return Response({"helpful_count": comment.helpful_count})
