
from task_manager.tasks.tasks import periodic_emailer
from django.test import TestCase
from django.contrib.auth import get_user_model
from task_manager.tasks.models import Task, Report
from datetime import datetime, time
from django.core import mail


User = get_user_model()


class TestCelery(TestCase):
    def test_email_report(self):
        users = [{
                "username":"test1",
                "email":"sh2@rbst.eu.org",
                "password":"test1_pass"
            },{
                "username":"test2",
                "email":"jsmith@rbst.eu.org",
                "password":"test2_pass",

            },
        ]
        user1 = User.objects.create_user(**users[0])
        user2 = User.objects.create_user(**users[1])

        hour = datetime.now().hour
        min = datetime.now().minute

        Task.objects.create(user=user1, title="test")
        Task.objects.create(user=user1, title="test", status="completed")
        Task.objects.create(user=user1, title="test", status="cancelled")
        Task.objects.create(user=user1, title="test", status="completed")
        Task.objects.create(user=user2, title="test")
        Task.objects.create(user=user2, title="test", status="in_progress")

        Report.objects.create(user=user1, consent=True, time=time(hour=hour, minute=min))
        Report.objects.create(user=user2, consent=True, time=time(hour=hour, minute=min))

        periodic_emailer()

        self.assertEqual(len(mail.outbox), 2)
        
        mail1, mail2 = mail.outbox

        self.assertIn("1 pending", mail1.body)
        self.assertIn("2 completed", mail1.body)
        self.assertIn("1 cancelled", mail1.body)

        self.assertIn("1 pending", mail2.body)
        self.assertIn("1 in progress", mail2.body)