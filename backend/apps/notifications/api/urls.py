from django.urls import path

from apps.notifications.api.views import MyNotificationsView

urlpatterns = [
    path("mine/", MyNotificationsView.as_view(), name="notifications-mine"),
]
