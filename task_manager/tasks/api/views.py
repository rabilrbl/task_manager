
from http.client import responses
from task_manager.tasks.models import History, Task, STATUS_CHOICES
from django.contrib.auth import get_user_model

User = get_user_model()

from rest_framework.serializers import ModelSerializer

from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.views import APIView

from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import (
    DjangoFilterBackend, FilterSet,
    CharFilter, ChoiceFilter, IsoDateTimeFilter,
)

from django.utils.decorators import method_decorator
from drf_yasg.utils import swagger_auto_schema

class FilterClass(FilterSet):
    title = CharFilter(lookup_expr="icontains")
    completed = ChoiceFilter(
        label="Completion",
        choices=(
            (True, "Completed tasks"),
            (False, "Non-completed tasks"),
        )
    )
    status = ChoiceFilter(choices=STATUS_CHOICES)


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        ref_name = "user"
        fields = ("name", "username")


class TaskSerializer(ModelSerializer):

    user = UserSerializer(read_only=True)
    status = ChoiceFilter(choices=STATUS_CHOICES)

    class Meta:
        model = Task
        fields = [
            "id", "title", "priority",
            "description", "date_created",
            "status", "user",
        ]

@method_decorator(name="list", decorator=swagger_auto_schema(
    operation_description="List all tasks",
))
class TaskViewSet(ModelViewSet):

    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    permission_classes = (IsAuthenticated,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterClass

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, deleted=False)

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        return instance.soft_delete()


class HistoryFilter(FilterSet):
    # Filter date and time
    change_date = IsoDateTimeFilter(label="Modified Date Time")
    new_status = ChoiceFilter(choices=STATUS_CHOICES)
    old_status = ChoiceFilter(choices=STATUS_CHOICES)


class HistTaskSer(ModelSerializer):
    class Meta:
        model = Task
        fields = ["title", "priority", "description", "date_created"]


class HistorySerializer(ModelSerializer):

    class Meta:
        model = History
        fields = ["id", "change_date", "old_status", "new_status"]


class HistoryViewSet(ReadOnlyModelViewSet):

    permission_classes = (IsAuthenticated,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = HistoryFilter
    serializer_class = HistorySerializer

    queryset = History.objects.all()

    def get_queryset(self):
        # allow access to only the user's history
        return History.objects.filter(
            task=self.kwargs["history_pk"],
            task__user=self.request.user, task__deleted=False,
        ).order_by("-change_date")
