
from http.client import responses
from urllib import response

from django.contrib.auth import get_user_model

from task_manager.tasks.models import (
    PRIORITY_CHOICES,
    STATUS_CHOICES,
    Board,
    History,
    Task,
)

User = get_user_model()

from django_filters.rest_framework import (
    CharFilter,
    ChoiceFilter,
    DjangoFilterBackend,
    FilterSet,
    IsoDateTimeFilter,
)
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.serializers import BaseSerializer, ModelSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

# Import Count and Response
from rest_framework.response import Response


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
    priority = ChoiceFilter(choices=PRIORITY_CHOICES)
    board = ChoiceFilter(choices=Board.objects.filter(deleted=False).values_list("id", "title"))


class UserSerializer(BaseSerializer):
    class Meta:
        model = User
        ref_name = "user"
        fields = ("name", "username")

class ShortBoardSerializer(ModelSerializer):
    class Meta:
        model = Board
        fields = ("id", "title")


class TaskSerializer(ModelSerializer):

    status = ChoiceFilter(choices=STATUS_CHOICES)
    priority = ChoiceFilter(choices=PRIORITY_CHOICES)
    created_by = UserSerializer(read_only=True)
    board = ShortBoardSerializer(read_only=True)


    class Meta:
        model = Task
        fields = [
            "id", "title", "priority",
            "description", "date_created",
            "status", "created_by", "board"
        ]

class TaskViewSet(ModelViewSet, APIView):
    """

    All tasks operations are performed by the user who created the task.

    """


    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    permission_classes = (IsAuthenticated,)

    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterClass

    # define custom tag for swagger documentation of this viewset
    # https://www.django-rest-framework.org/api-guide/swagger/


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


class BoardFilterClass(FilterSet):
    title = CharFilter(lookup_expr="icontains")

class BoardViewSet(ModelViewSet):
    
        permission_classes = (IsAuthenticated,)
    
        queryset = Board.objects.all()
        serializer_class = BoardSerializer
        filter_backends = (DjangoFilterBackend,)
        filterset_class = BoardFilterClass
    
        def get_queryset(self):
            return Board.objects.filter(user=self.request.user, deleted=False)
    
        def perform_create(self, serializer):
            return serializer.save(user=self.request.user)
    
        def perform_destroy(self, instance):
            return instance.soft_delete()

class GetTasksCount(APIView):
    """
    Returns the number of tasks in each board
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        """
        Returns the number of tasks in each board
        """
        total_tasks = Task.objects.filter(user=request.user, deleted=False).count()
        todo_tasks = Task.objects.filter(user=request.user, status="pending", deleted=False).count()
        onprogress_tasks = Task.objects.filter(user=request.user, status="in_progress", deleted=False).count()
        done_tasks = Task.objects.filter(user=request.user, status="completed", deleted=False).count()

        response_json = {
            "user": request.user.username,
            "total": total_tasks,
            "todo": todo_tasks,
            "onprogress": onprogress_tasks,
            "done": done_tasks,
        }

        return Response(response_json, status=200)

