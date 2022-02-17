from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

from django.db.models import signals
from django.dispatch import receiver

from uuid import uuid4
from datetime import time

STATUS_CHOICES = (
    ("pending", "Pending"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
)


class History(models.Model):

    task = models.ForeignKey("Task", on_delete=models.CASCADE)
    old_status = models.CharField(
        max_length=100, choices=STATUS_CHOICES, default="n/a")
    new_status = models.CharField(
        max_length=100, choices=STATUS_CHOICES, default="n/a")
    change_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.task.title


class Task(models.Model):
    external_id = models.UUIDField(
        default=uuid4, unique=True, db_index=True, editable=False)
    title = models.CharField(max_length=100)
    priority = models.IntegerField(default=0)
    description = models.TextField(max_length=500, blank=True)
    completed = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    deleted = models.BooleanField(default=False)
    status = models.CharField(
        max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0])
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def soft_delete(self):
        self.deleted = True
        self.save()
    
    def delete(self):
        self.deleted = True
        self.save()

    def save(self, *args, **kwargs):
        # prevent priority collision
        pr = self.priority
        status = self.status
        user = self.user
        taskList = []  # store tasks to update
        try:
            taskCheck = Task.objects.get(
                priority=pr, status=status, user=user, deleted=False)
            if taskCheck.pk == self.pk and taskCheck.priority == self.priority:
                raise Task.DoesNotExist
            while taskCheck:  # keep finding until DoesNotExist
                pr += 1  # increase priority
                taskCheck.priority = pr  # increment priority
                taskList.append(taskCheck)  # append task to update
                taskCheck = Task.objects.get(
                    priority=pr, status=status,
                    user=user, deleted=False)  # update to next task
        except Task.DoesNotExist:  # on error
            pass  # skip
        if taskList:
            Task.objects.bulk_update(taskList, ['priority'])  # save at once

        # mark completed
        self.completed = self.status == "completed"

        super(Task, self).save(*args, **kwargs)


class Report(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,)
    consent = models.BooleanField(
        default=False, help_text="Uncheck to stop receiving reports")
    time = models.TimeField(
        default=time(0, 0, 0), help_text="All times are in UTC format.")

    def __str__(self) -> str:
        return self.user.username


# pre_save to store old_status
@receiver(signals.pre_save, sender=Task)
def task_pre_save(sender, instance, **kwargs):
    if instance.pk:
        old_status = sender.objects.get(pk=instance.pk).status
        if old_status != instance.status:
            history = History.objects.create(
                task=instance, new_status=instance.status,
                old_status=old_status)
            history.save()
