from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from task_manager.tasks.models import Task
from django.contrib.auth import get_user_model

User = get_user_model()

class BaseApiTest(APITestCase):
    def setUp(self) -> None:
        self.request = APIClient()
        self.user = User.objects.create_user(username="apitest", email="api@test.in",  password="api_test", first_name="Api", last_name="Test")
        return super().setUp()

    def test_unauthorizedViews(self):
        response = self.request.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.request.get("/api/tasks/1/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.request.get("/api/tasks/1/history/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_tasksList(self):
        self.request.login(username="apitest", password="api_test")

        response = self.request.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(),[])

        task1 = Task.objects.create(title="Task1", description="test_description", user=self.user)
        task2 = Task.objects.create(title="Task2", user=self.user)

        # All task list view
        response = self.request.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(task1.title, response.json()[0]['title'])
        self.assertEqual(task2.title, response.json()[1]['title'])

        self.assertNotEqual(response.json()[0]['priority'],response.json()[1]['priority'])

        # specific task details view
        response = self.request.get(f"/api/tasks/{task1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(task1.title, response.json()['title'])
        # priority will be incremented on collision
        self.assertEqual(int(task1.priority)+1, response.json()['priority'])
        self.assertEqual(task1.description, response.json()['description'])
        self.assertEqual(task1.user.username, response.json()['user']['username'])
        self.assertEqual(task1.user.name, response.json()['user']['name'])

        task1_response = response.json()
        
        response = self.request.get(f"/api/tasks/{task2.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(task2.title, response.json()['title'])
        self.assertEqual(int(task2.priority), response.json()['priority'])
        self.assertEqual(task2.description, response.json()['description'])
        self.assertEqual(task2.user.username, response.json()['user']['username'])
        self.assertEqual(task2.user.name, response.json()['user']['name'])

        # Delete a task
        response = self.request.delete(f"/api/tasks/{task2.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Check for 404 error
        response = self.request.get(f"/api/tasks/{task2.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        task1_response.pop('user')
        task1_response['title'] = 'Task1_New'

        # Edit a task
        response = self.request.put(f"/api/tasks/{task1.id}/", data=task1_response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response.json()['title'], task1.title)
        self.assertEqual(response.json()['title'], task1_response['title'])

        # Create a new task
        new_task = {
            "title":"NewTask",
            "description":"new task desc",
            "status":"in_progress",
            "priority":2,
        }
        response = self.request.post("/api/tasks/", data=new_task)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(Task.objects.filter(id=response.json()['id']).exists())
        self.assertEqual(new_task['title'], response.json()['title'])
        self.assertEqual(new_task['description'], response.json()['description'])
        self.assertEqual(new_task['status'], response.json()['status'])
        self.assertEqual(int(new_task['priority']), response.json()['priority'])

    
class TestHistoryAPI(APITestCase):
    def setUp(self) -> None:
        self.request = APIClient()
        self.user = User.objects.create_user(username="apitest", email="api@test.in",  password="api_test", first_name="Api", last_name="Test")
        return super().setUp()

    def test_history(self):
        task1 = Task.objects.create(title="Task1", description="test_description", user=self.user)
        
        task1.status = "in_progress"
        task1.save()

        task1.status = "completed"
        task1.save()

        task1.status = "cancelled"
        task1.save()

        response = self.request.get(f"/api/tasks/{task1.id}/history/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.request.login(username="apitest", password="api_test")

        response = self.request.get(f"/api/tasks/{task1.id}/history/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.json()[0]['old_status'], "completed")
        self.assertEqual(response.json()[0]['new_status'], "cancelled")

        self.assertEqual(response.json()[1]['old_status'], "in_progress")
        self.assertEqual(response.json()[1]['new_status'], "completed")

        self.assertEqual(response.json()[2]['old_status'], "pending")
        self.assertEqual(response.json()[2]['new_status'], "in_progress")

        




        



