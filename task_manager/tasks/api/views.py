
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
from rest_framework.serializers import ModelSerializer, CharField
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
    # board = ChoiceFilter(choices=Board.objects.filter(deleted=False).values_list("id", "title"))


# class UserSerializer(ModelSerializer):
#     class Meta:
#         model = User
#         ref_name = "user"
#         fields = ("name", "username")


class TaskSerializer(ModelSerializer):

    status = ChoiceFilter(choices=STATUS_CHOICES)
    priority = ChoiceFilter(choices=PRIORITY_CHOICES)
    board_title = CharField(source="board.title", read_only=True)
    class Meta:
        model = Task
        fields = [
            "id", "title", "priority",
            "description", "date_created",
            "status", "board", "board_title"
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
        id = self.kwargs["board_pk"] if "board_pk" in self.kwargs else None
        if id:
            return Task.objects.filter(user=self.request.user, board__deleted=False,deleted=False, board__id=id)
        return Task.objects.filter(user=self.request.user, board__deleted=False,deleted=False)

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
        id = self.kwargs["task_pk"] if "task_pk" in self.kwargs else None
        return History.objects.filter(task__user=self.request.user, task__deleted=False, task__id=id
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

        permission_classes = (IsAuthenticated,)

        response_json = {
            "user": request.user.name,
            "total": total_tasks,
            "todo": todo_tasks,
            "onprogress": onprogress_tasks,
            "done": done_tasks,
        }

        return Response(response_json, status=200)


class GetBoardsList(APIView):
    """
    Returns the list of boards
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        """
        Returns the list of boards
        """
        boards = Board.objects.filter(user=request.user, deleted=False).values("id", "title")
        count = boards.count()

        response_json = {
            "count": count,
            "boards": boards,
        }

        return Response(response_json, status=200)


