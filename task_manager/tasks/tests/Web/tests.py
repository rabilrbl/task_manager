from django.contrib.auth.models import AnonymousUser

from django.contrib.auth import get_user_model

User = get_user_model()

from task_manager.tasks.models import Task

from django.test import TestCase, RequestFactory, Client

from django.http.response import Http404
from django.shortcuts import reverse

# Web View
from task_manager.tasks.views import (
    GenericListView, CreateTaskView, 
    EditTaskView, TaskDetailView, 
    DeleteTaskView, CompleteTaskView,
    LoginView, SignUpView,

    GenericCompletedListView, GenericAllTaskView
)

# Api Views
from task_manager.tasks.views import (
    GenericListView,
)

class WebAuthTests(TestCase):

    def test_not_authenticated(self):
        """
        Try to GET the tasks listing page, expect the response to redirect to the login page
        """
        authenticated_endpoints = [
            'tasks',
            'add-task',
            'completed-tasks',
            'all-tasks',
            'reports',
            'create-task',
        ]

        redirect_url = "/user/login/?next="

        for uri in authenticated_endpoints:
            uri = reverse(uri)
            response = self.client.get(uri)
            self.assertRedirects(response, redirect_url+uri)
        
        # endpoints with arguments
        authenticated_endpoints = [
            'edit-task',
            'detail-view',
            'delete-task',
            'complete-task',
        ]

        for uri in authenticated_endpoints:
            uri = reverse(uri, args=[1])
            response = self.client.get(uri)
            self.assertRedirects(response, redirect_url+uri)

        non_auth_uris = [

            '/user/login/',
            '/user/signup/',
        ]
        for uri in non_auth_uris:
            response = self.client.get(uri)
            self.assertEqual(response.status_code, 200)

class WebAuthorizedTests(TestCase):
    def setUp(self) -> None:
        """Initialize"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username="bruce_wayne", email="bruce@wayne.org", password="i_am_batman")
        # Create an instance of a GET request.
        self.request = self.factory.get("/")
        # Set the user instance on the request.
        self.request.user = self.user

        self.task1 = Task.objects.create(priority=1,title="This is a long test task name", description="test description", user=self.user)

        self.user2 = User.objects.create_user(username="authtest", email="authtest@test.in", password="authtestsecret")
        self.task2 = Task.objects.create(priority=2, title="This is a second task name", description="test description", user=self.user2)


    def test_login_view(self):
        """
        Test Login Page components
        """
        request = self.factory.get("/user/login/")
        request.user = AnonymousUser()
        response = LoginView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        response_content = response.render().content.decode()
        self.assertInHTML("Login", response_content)
        self.assertInHTML("Username", response_content, 1)
        self.assertInHTML("Password", response_content, 1)

    def test_signup_view(self):
        """
        Test Signup Page components
        """
        request = self.factory.get("/user/signup/")
        request.user = AnonymousUser()
        response = SignUpView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        response_content = response.render().content.decode()
        self.assertInHTML("Name", response_content)
        self.assertInHTML("Username", response_content)
        self.assertInHTML("Email", response_content)
        self.assertInHTML("Password", response_content)
        self.assertInHTML("Confirm Password", response_content)
        self.assertInHTML("terms and conditions", response_content)

    
    def test_generic_view_components(self):
        """
        Check generic view components
        """
        response = GenericListView.as_view()(self.request)
        self.assertEqual(response.status_code, 200)

        response = GenericCompletedListView.as_view()(self.request)
        self.assertEqual(response.status_code, 200)

        response = GenericAllTaskView.as_view()(self.request)
        self.assertEqual(response.status_code, 200)

    def test_create_task_view(self):
        """
        Test Create Task View
        """
        response = CreateTaskView.as_view()(self.request)
        self.assertEqual(response.status_code, 200)
        response_content = response.render().content.decode()
        self.assertInHTML("Title", response_content)
        self.assertInHTML("Priority", response_content)
        self.assertInHTML("Description", response_content)
        self.assertInHTML("Status", response_content)
    
    def test_edit_task_view(self):
        """
        Test Edit Task View
        """
        response = EditTaskView.as_view()(self.request, pk=self.task1.pk)
        self.assertEqual(response.status_code, 200)
        response_content = response.render().content.decode()
        self.assertIn(self.task1.title, response_content)
        self.assertInHTML(self.task1.description, response_content)

    def test_detail_view(self):
        """
        Test Detail Task View
        """
        response = TaskDetailView.as_view()(self.request, pk=self.task1.pk)
        self.assertEqual(response.status_code, 200)
        response_content = response.render().content.decode()
        self.assertInHTML(self.task1.title, response_content)
        self.assertInHTML(self.task1.description, response_content)

    def test_complete_view(self):
        """
        Test Mark Complete View
        """
        response = CompleteTaskView.as_view()(self.request, slug=self.task1.external_id)
        self.assertEqual(response.status_code, 302)

    def test_delete_view(self):
        """
        Test Delete Task Component
        """
        response = DeleteTaskView.as_view()(self.request, pk=self.task1.pk)
        self.assertEqual(response.status_code, 200)
        response_content = response.render().content.decode()
        self.assertInHTML(f'"{self.task1.title}"', response_content)
        self.assertInHTML("Delete", response_content)
        self.assertInHTML("Cancel", response_content)
    
    def test_soft_delete(self):
        """
        Test Soft Delete in views
        """
        # Test soft delete
        self.task1.deleted=True
        self.task1.save()

        self.assertRaises(Http404, TaskDetailView.as_view(), self.request, pk=self.task1.pk)
        self.assertRaises(Http404, EditTaskView.as_view(), self.request, pk=self.task1.pk)
        self.assertRaises(Http404, DeleteTaskView.as_view(), self.request, pk=self.task1.pk)

    def test_error_generic_view_components(self):
        """
        Unauthorized and Random Cases
        """
        # unauthorized access
        self.assertRaises(Http404,  EditTaskView.as_view(), self.request, pk=self.task2.pk)
        self.assertRaises(Http404,  TaskDetailView.as_view(), self.request, pk=self.task2.pk)
        self.assertRaises(Http404, CompleteTaskView.as_view(), self.request, slug=self.task2.external_id)
        self.assertRaises(Http404,  DeleteTaskView.as_view(), self.request, pk=self.task2.pk)

        # random value test
        self.assertRaises(Http404, TaskDetailView.as_view(), self.request, pk=99)
        self.assertRaises(Http404, EditTaskView.as_view(), self.request, pk=101)
        self.assertRaises(Http404, DeleteTaskView.as_view(), self.request, pk=13)



class TasksLogicTests(TestCase):
    def setUp(self) -> None:
        self.request = Client()
        self.user = User.objects.create_user(username="testfs", email="test@test.in", password="test_secret")
        self.request.login(username="testfs", password="test_secret")
        self.task_data = {
            "title": "Task1",
            "priority": "1",
            "status": "in_progress",
            "description": "test description of the task",
        }
        return super().setUp()
    
    def test_taskCreateView(self):
        """
        Creates two new tasks and check if present in pending view
        """
        response = self.request.get(reverse('tasks'))
        self.assertContains(response, "You have no tasks", status_code=200)

        # create first task and verify with model
        post_data = {
            "title": "Task1",
            "priority": 1,
            "status": "pending",
            "next": "/tasks/",
            "description": "test description of the task",
        }
        url = reverse('create-task')
        response = self.request.post(url, post_data)
        self.assertRedirects(response, post_data['next'])
        task1 = Task.objects.get(user=self.user, title=post_data['title'])
        task1.save()
        self.assertEqual(task1.title, post_data['title'])
        self.assertEqual(task1.priority, post_data['priority'])
        self.assertEqual(task1.status, post_data['status'])
        self.assertEqual(task1.description, post_data['description'])
        self.assertEqual(task1.completed, False)

        post_data['title'] = "Task2"
        post_data['priority'] = 2
        response = self.request.post(url, post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        task2 = Task.objects.get(title=post_data['title'])

    
    def test_detailView(self):
        task1 = Task.objects.create(**self.task_data , user=self.user)
        response = self.request.get(reverse('detail-view', args=[task1.external_id]))
        self.assertEqual(response.status_code, 200)
        response_data = response.render().content.decode()
        self.assertInHTML(self.task_data['title'], response_data)
        self.assertInHTML(self.task_data['priority'], response_data)
        self.assertInHTML(self.task_data['status'], response_data)
        self.assertInHTML(self.task_data['description'], response_data)

    def test_edit_taskView(self):
        task1 = Task.objects.create(**self.task_data , user=self.user)
        task1.status = "pending"
        task1.save()
        
        edit_task_data = self.task_data
        edit_task_data['title'] = 'new_title'
        edit_task_data['priority'] = 8
        edit_task_data['description'] = "New Description"
        edit_task_data['status'] = "completed"

        response = self.request.post(reverse('edit-task', args=[task1.external_id]), data=edit_task_data, follow=True)
        self.assertEqual(response.status_code, 200)
        task1 = Task.objects.get(pk=task1.id)
        self.assertEqual(task1.title, edit_task_data['title'])
        self.assertEqual(task1.priority, edit_task_data['priority'])
        self.assertEqual(task1.description, edit_task_data['description'])
        self.assertEqual(task1.status, edit_task_data['status'])

    def test_completedView(self):
        task1 = Task.objects.create(**self.task_data , user=self.user)

        self.assertFalse(task1.completed)

        response = self.request.get(reverse('complete-task', args=[task1.external_id]))
        self.assertRedirects(response, "/tasks/", target_status_code=200)

        task1 = Task.objects.get(pk=task1.id)

        self.assertTrue(task1.completed)
    
    def test_deleteView(self):
        task1 = Task.objects.create(**self.task_data , user=self.user)

        response = self.request.get(reverse('delete-task', args=[task1.external_id]))
        self.assertContains(response, task1.title, status_code=200)

        response = self.request.post(reverse('delete-task', args=[task1.external_id]))
        self.assertRedirects(response, "/tasks/", target_status_code=200)

        self.assertTrue(Task.objects.get(id=task1.id).deleted)
        self.assertFalse(Task.objects.filter(id=task1.id, deleted=False, user=self.user).exists())

    def test_pendingListView(self):
        self.task_data['priority']=1
        self.task_data['status']="pending"
        task1 = Task.objects.create(**self.task_data , user=self.user)
        self.task_data['title']="Task2"
        task2 = Task.objects.create(**self.task_data, user=self.user)

        response = self.request.get(reverse('tasks'))
        response_data = response.render().content.decode()
        self.assertInHTML("0 of 2 tasks completed", response_data)
        self.assertInHTML(task1.title, response_data)
        self.assertInHTML(task2.title, response_data)

    def test_TaskListViews(self):
        self.task_data['priority']=1
        self.task_data['status']="pending"
        task1 = Task.objects.create(**self.task_data , user=self.user)

        # Pending View
        response = self.request.get(reverse('tasks'))
        response_data = response.render().content.decode()
        self.assertInHTML("0 of 1 tasks completed", response_data)
        self.assertInHTML(task1.title, response_data)  

        self.task_data['title']="Task2"
        self.task_data['status']="completed"
        task2 = Task.objects.create(**self.task_data, user=self.user)   

        # Completed  View
        response = self.request.get(reverse('completed-tasks'))
        response_data = response.render().content.decode()
        self.assertInHTML("1 of 2 tasks completed", response_data)
        self.assertInHTML(task2.title, response_data)  
        self.assertNotIn(task1.title, response_data)


        self.task_data['title']="Task3"
        self.task_data['status']="in_progress"
        task3 = Task.objects.create(**self.task_data, user=self.user)   
        self.task_data['title']="Task4"
        self.task_data['status']="cancelled"
        task4 = Task.objects.create(**self.task_data, user=self.user) 

        # All task views
        response = self.request.get(reverse('all-tasks'))
        response_data = response.render().content.decode()
        self.assertInHTML("1 of 4 tasks completed", response_data)
        self.assertInHTML(task1.title, response_data)
        self.assertInHTML(task2.title, response_data) 
        self.assertInHTML(task3.title, response_data) 
        self.assertInHTML(task4.title, response_data) 

        for task in Task.objects.all():
            task.soft_delete()
        
        response = self.request.get(reverse('all-tasks'))
        response_data = response.render().content.decode()
        self.assertInHTML("0 of 0 tasks completed", response_data)
        self.assertInHTML("You have no tasks.", response_data)
