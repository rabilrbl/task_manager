
from http.client import responses
from task_manager.tasks.models import Board, History, Task, STATUS_CHOICES, PRIORITY_CHOICES
from django.contrib.auth import get_user_model

User = get_user_model()

from rest_framework.serializers import BaseSerializer, ModelSerializer

from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import (
    DjangoFilterBackend, FilterSet,
    CharFilter, ChoiceFilter, IsoDateTimeFilter,
)


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


class UserSerializer(BaseSerializer):
    class Meta:
        model = User
        ref_name = "user"
        fields = ("name", "username")


class TaskSerializer(ModelSerializer):

    status = ChoiceFilter(choices=STATUS_CHOICES)
    priority = ChoiceFilter(choices=PRIORITY_CHOICES)
    created_by = UserSerializer(read_only=True)


    class Meta:
        model = Task
        fields = [
            "id", "title", "priority",
            "description", "date_created",
            "status", "created_by", "board"
        ]

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

class BoardSerializer(ModelSerializer):
    class Meta:
        model = Board
        fields = ["id", "title", "description" , "created_at"]


class BoardViewSet(ModelViewSet):
    
        permission_classes = (IsAuthenticated,)
    
        queryset = Board.objects.all()
        serializer_class = BoardSerializer
    
        def get_queryset(self):
            return Board.objects.filter(user=self.request.user, deleted=False)
    
        def perform_create(self, serializer):
            return serializer.save(user=self.request.user)
    
        def perform_destroy(self, instance):
            return instance.soft_delete()


