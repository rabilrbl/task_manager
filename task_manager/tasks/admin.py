from django.contrib import admin

# Register your models here.
from .models import Task, History, Report
admin.site.register(Task)
admin.site.register(History)
admin.site.register(Report)
