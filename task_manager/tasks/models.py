from asyncio import tasks
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

from django.db.models import signals
from django.dispatch import receiver

from uuid import uuid4
from datetime import datetime, time, tzinfo
import pytz

# STATUS_CHOICES = (
#     ("pending", "Pending"),
#     ("in_progress", "In Progress"),
#     ("completed", "Completed"),
#     ("cancelled", "Cancelled"),
# )

PRIORITY_CHOICES = (
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
)

class History(models.Model):

    task = models.ForeignKey("Task", on_delete=models.CASCADE)
    old_status = models.ForeignKey("Status", on_delete=models.CASCADE, related_name="old_status")
    new_status = models.ForeignKey("Status", on_delete=models.CASCADE, related_name="new_status")
    change_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.task.title

class Status(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey(User , on_delete=models.CASCADE , null=True,blank=True)
    board = models.ForeignKey("Board", on_delete=models.CASCADE)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        self.deleted = True
        self.save()

    def __str__(self):
        return self.title


class Task(models.Model):
    external_id = models.UUIDField(
        default=uuid4, unique=True, db_index=True, editable=False
    )
    title = models.CharField(max_length=100)
    priority = models.CharField(max_length=100, choices=PRIORITY_CHOICES)
    description = models.TextField(max_length=500, blank=True)
    completed = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    status = models.ForeignKey(Status, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    board = models.ForeignKey("Board", on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def soft_delete(self):
        self.deleted = True
        self.save()

    def delete(self):
        self.deleted = True
        self.save()


class Board(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # def soft_delete(self):
    #     self.deleted = True
    #     self.save()

    def delete(self):
        self.deleted = True
        self.save()

    def __str__(self):
        return self.title


class Report(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    consent = models.BooleanField(
        default=False, help_text="Uncheck to stop receiving reports"
    )
    send_time = models.DateTimeField(
        default=datetime.now(tz=pytz.UTC).strftime("%Y-%m-%d %H:%M:00"),
        help_text="Enter UTC time in HH:MM",
        editable=True,
        blank=True,
    )

    def __str__(self) -> str:
        return self.user.username


# pre_save to store old_status
@receiver(signals.pre_save, sender=Task)
def task_pre_save(sender, instance, **kwargs):
    if instance.pk:
        old_status = sender.objects.get(pk=instance.pk).status
        if old_status != instance.status:
            history = History.objects.create(
                task=instance, new_status=instance.status, old_status=old_status
            )
            history.save()
