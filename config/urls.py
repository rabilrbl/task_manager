from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token

from task_manager.tasks.views import (
     index, GenericListView, CreateTaskView,
     EditTaskView, GenericAllTaskView,
     GenericCompletedListView,
     TaskDetailView, DeleteTaskView, CompleteTaskView,
     CreateTimeView, LoginView, SignUpView, GenericCancelledListView, GenericInProgressListView
)

from task_manager.tasks.api.views import TaskViewSet, HistoryViewSet

from rest_framework_nested import routers
# import DefaultRouter
from rest_framework.routers import DefaultRouter


urlpatterns = [
    path("", TemplateView.as_view(template_name="pages/home.html"), name="home"),
    path("__reload__/", include("django_browser_reload.urls")),
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path("users/", include("task_manager.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),
    path("user/signup/", SignUpView.as_view(), name="signup"),
    path("user/login/", LoginView.as_view(), name="login"),
    # Your stuff: custom urls includes go here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
    # DRF auth token
    path("auth-token/", obtain_auth_token),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="api-schema"),
        name="api-docs",
    ),
]

router = DefaultRouter()
router.register(r'api/tasks', TaskViewSet, basename='tasks')
client_router = routers.NestedSimpleRouter(
     router, r'api/tasks', lookup='history',
)
client_router.register(r'history', HistoryViewSet, basename="history")


# Api views
urlpatterns += [
    path("admin/", admin.site.urls),

    # Browser based view
    path("", index, name="index"),
    # path("__reload__/", include("django_browser_reload.urls")),
    path("add-task/", CreateTaskView.as_view(), name="add-task"),
    path("create-task/", CreateTaskView.as_view(), name="create-task"),
    path("edit-task/<slug>/", EditTaskView.as_view(), name="edit-task"),
    path("detail-view/<slug>/", TaskDetailView.as_view(), name="detail-view"),
    path("delete-task/<slug>/", DeleteTaskView.as_view(), name="delete-task"),
    path("complete-task/<slug>/",
         CompleteTaskView.as_view(), name="complete-task"),
    path("tasks/", GenericListView.as_view(), name="tasks"),
    path("completed-tasks/", GenericCompletedListView.as_view(),
         name="completed-tasks"),
    path("all-tasks/", GenericAllTaskView.as_view(), name="all-tasks"),
    path("in-progress/", GenericInProgressListView.as_view(), name="in-progress"),
    path("cancelled/", GenericCancelledListView.as_view(), name="cancelled"),
    path("reports/", CreateTimeView.as_view(), name="reports"),
] + router.urls + client_router.urls

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
