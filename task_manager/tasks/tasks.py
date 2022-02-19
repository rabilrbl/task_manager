
from datetime import datetime, time, timedelta
from django.core.mail import send_mail
from task_manager.tasks.models import Task, Report
from celery.decorators import periodic_task

# from config import celery_app as app


def send_email_report(self, report) -> None:
    user = report.user
    task = Task.objects.filter(user=user, deleted=False)
    print(f"Sending email reminder to {user.username}\n")
    pending_tasks = task.filter(status="pending").count()
    completed_tasks = task.filter(status="completed").count()
    in_progress_tasks = task.filter(status="in_progress").count()
    cancelled_tasks = task.filter(status="cancelled").count()
    email_content = f"""
        Hi {user.username},
        \n\nYou have {pending_tasks} pending tasks,
        {completed_tasks} completed tasks,
        {in_progress_tasks} in progress tasks,
        {cancelled_tasks} cancelled tasks.
        \n\nRegards,\nTask Manager
    """
    send_mail(
        "Task Manager Report",
        (email_content),
        "tasks@gdctasks.com",
        [user.email],
        fail_silently=False,  # Throw exception if email fails to send
    )
    # increment by a day
    report.send_time += timedelta(days=1)
    print("Email sent to {}".format(user.email))


@periodic_task(run_every=timedelta(minute=1))
def periodic_emailer():
    currentTime = datetime.now()
    print("Checking time for user daily report......")
    reports = Report.objects.filter(
        send_time__lte=currentTime,
        consent=True
    )
    for rpt in reports:
        send_email_report(rpt)

# Design a email scheduler for daily report and retry on server failure
# https://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#task-scheduling
# https://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#task-scheduling-decorators
