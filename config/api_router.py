from django.conf import settings
from rest_framework.routers import DefaultRouter, SimpleRouter
from task_manager.tasks.api.views import BoardViewSet, HistoryViewSet, TaskViewSet

from task_manager.users.api.views import UserViewSet
from rest_framework_nested import routers

if settings.DEBUG:
    router = DefaultRouter()
else:
    router = SimpleRouter()

app_name = "api"

router.register("users", UserViewSet)

router.register(r'boards', BoardViewSet)
router.register(r'tasks', TaskViewSet)
board_router = routers.NestedSimpleRouter(router, r'boards', lookup='board')
board_router.register(r'tasks', TaskViewSet)
client_router = routers.NestedSimpleRouter(board_router, r'tasks', lookup='task')
client_router.register(r'history', HistoryViewSet)


urlpatterns =  router.urls + client_router.urls + board_router.urls
