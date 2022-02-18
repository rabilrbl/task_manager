
from django.shortcuts import redirect, render
from django.views import View
from django.http import HttpResponseRedirect
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from django.shortcuts import get_object_or_404

from django.views.generic.detail import DetailView

from django.forms import ModelForm, ValidationError
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django import forms
from task_manager.tasks.models import Task, Report

from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.auth import get_user_model


User = get_user_model()


class AuthorizedUserMixin(LoginRequiredMixin):
    slug_field = 'external_id'

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user, deleted=False)

    def get_success_url(self):
        _from = self.request.POST.get('next')
        return _from if _from else '/tasks/'


def index(request):
    return render(request, 'index.html')


class LoginView(LoginView):
    template_name = 'login.html'

    # allow only for unauthenticated users
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/tasks/')
        return super().dispatch(request, *args, **kwargs)

    # Add class attributes to customize the form

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add the form field to the form
        form.fields['username'].widget.attrs.update(
            {
                'class': '''
                    w-full px-4 py-2 bg-gray-50 border
                    border-gray-300 rounded-full shadow-lg
                    shadow-blue-100 focus:shadow-blue-200
                    focus:outline-none focus:shadow-outline
                    ring-blue-500 focus:bg-white focus:ring-2
                '''
            }
        )
        form.fields['password'].widget.attrs.update(
            {
                'class': '''
                    w-full px-4 py-2 bg-gray-50
                    border border-gray-300 rounded-full
                    shadow-lg shadow-blue-100 focus:shadow-blue-200
                    focus:outline-none focus:shadow-outline
                    ring-blue-500 focus:bg-white focus:ring-2
                '''
            }
        )
        return form


class UserSignUpForm(UserCreationForm):
    terms = forms.BooleanField(required=True)
    reports = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ('username', 'name', 'email',
                  'password1', 'password2', 'terms', 'reports')


class SignUpView(CreateView):
    form_class = UserSignUpForm
    success_url = '/user/login'
    template_name = 'signup.html'

    formCssClass = """
        w-full px-4 py-2 bg-gray-50
        border border-gray-300 rounded-lg
        shadow-lg shadow-blue-100 focus:shadow-blue-200
        focus:outline-none focus:shadow-outline
        ring-blue-500 focus:bg-white
        focus:ring-2
    """
    checkboxCssClass = '''
        bg-gray-50 cursor-pointer focus:bg-white
        px-4 py-2 shadow-lg shadow-blue-200
        hover:ring-blue-300 h-5 w-5 bg-blue-500
        text-white accent-blue-500 focus:outline-none
        focus:shadow-outline
    '''
    # allow only for unauthenticated users

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('/tasks/')
        return super().dispatch(request, *args, **kwargs)

    # Add class attributes to the form
    def get_form(self, form_class=None):
        form = super(SignUpView, self).get_form()
        form.fields['username'].widget.attrs.update(
            {'class': self.formCssClass})
        form.fields['password1'].widget.attrs.update(
            {'class': self.formCssClass})
        form.fields['password2'].widget.attrs.update(
            {'class': self.formCssClass})
        form.fields['email'].widget.attrs.update(
            {
                'class': self.formCssClass,
                'placeholder': 'Mail Address',
                'required': True,
            }
        )
        form.fields['name'].widget.attrs.update(
            {
                'class': self.formCssClass,
                'placeholder': 'Full Name',
            }
        )
        form.fields['terms'].widget.attrs.update(
            {
                'class': self.checkboxCssClass,
                'placeholder': 'I agree to the terms and conditions',
            }
        )
        form.fields['reports'].widget.attrs.update(
            {
                'class': self.checkboxCssClass,
                'placeholder': 'I want to receive reports',
            }
        )
        return form

    def form_valid(self, form):
        # if reports checkbox is checked redirect to reports page
        if form.cleaned_data['reports']:
            self.success_url = '/user/login?next=/reports'
        return super(SignUpView, self).form_valid(form)


class TaskCreateForm(ModelForm):
    # Add class attributes to customize the form
    def __init__(self, *args, **kwargs):
        super(TaskCreateForm, self).__init__(*args, **kwargs)
        self.fields['title'].widget.attrs.update(
            {
                'class': '''
                    bg-gray-50 focus:bg-white border
                    border-gray-200 rounded-lg px-4 py-2 focus:ring
                    shadow-lg focus:ring-blue-400 shadow-blue-200
                    focus:outline-none focus:shadow-outline w-full
                '''
            }
        )
        self.fields['priority'].widget.attrs.update(
            {
                'class': '''
                    bg-gray-50 focus:bg-white border
                    border-gray-200 rounded-lg px-4 py-2
                    focus:ring shadow-lg focus:ring-blue-400
                    shadow-blue-200 focus:outline-none
                    focus:shadow-outline w-full'''
            }
        )
        self.fields['description'].widget.attrs.update(
            {
                'class': '''
                    caret-blue-500 bg-gray-50 focus:bg-white
                    border border-gray-200 rounded-lg px-4 py-2
                    focus:ring shadow-lg focus:ring-blue-400 shadow-blue-200
                    focus:outline-none focus:shadow-outline w-full'''
            }
        )
        self.fields['status'].widget.attrs.update(
            {
                'class': '''
                    bg-gray-50 py-1 text-center rounded-lg
                    shadow-lg border border-gray-200 focus:ring
                    focus:ring-blue-400 shadow-blue-200 hover:ring-blue-300
                    text-blue-500 focus:outline-none focus:shadow-outline'''
            }
        )

    class Meta:
        model = Task
        fields = ['title', 'priority', 'description', 'status']

    def clean_title(self):
        title = self.cleaned_data['title']
        if len(title) < 5:
            raise ValidationError(
                "Task title must be at least 5 characters long.")
        return title


class CreateTaskView(AuthorizedUserMixin, CreateView):
    form_class = TaskCreateForm
    template_name = 'create_task.html'

    def form_valid(self, form):
        # set the user
        form.instance.user = self.request.user
        return super().form_valid(form)


class EditTaskView(AuthorizedUserMixin, UpdateView):
    model = Task
    form_class = TaskCreateForm
    template_name = 'edit_task.html'

# Detailed view of a task


class TaskDetailView(AuthorizedUserMixin, DetailView):
    model = Task
    template_name = 'task_detail.html'


# Delete a task

class DeleteTaskView(AuthorizedUserMixin, DeleteView):
    model = Task
    template_name = 'delete_task.html'

    # override the delete method to perform soft delete
    def form_valid(self, form):
        self.object = self.get_object()
        self.object.soft_delete()
        return HttpResponseRedirect(self.get_success_url())

# Complete a task


class CompleteTaskView(AuthorizedUserMixin, View):
    def get(self, request, *args, **kwargs):
        task = get_object_or_404(
            self.get_queryset(), external_id=self.kwargs['slug'])
        task.status = "completed"
        task.save()
        _from = request.GET.get('next')
        return redirect(_from) if _from else redirect('/tasks/')

# View all tasks


class GenericListView(AuthorizedUserMixin, ListView):
    template_name = 'tasks.html'
    context_object_name = 'tasks'
    paginate_by = 5

    def get_queryset(self):
        search_query = self.request.GET.get('search')
        tasks = super().get_queryset().filter(
            status='pending', completed=False).order_by('priority')
        if search_query:
            tasks = tasks.filter(title__icontains=search_query)
        return tasks

# View all completed tasks


class GenericCompletedListView(AuthorizedUserMixin, ListView):
    template_name = 'tasks.html'
    context_object_name = 'tasks'
    paginate_by = 5

    def get_queryset(self):
        search_query = self.request.GET.get('search')
        tasks = super().get_queryset().filter(
            status='completed'
            ).order_by('priority')
        if search_query:
            tasks = tasks.filter(title__icontains=search_query)
        return tasks

class GenericInProgressListView(AuthorizedUserMixin, ListView):
    template_name = 'tasks.html'
    context_object_name = 'tasks'
    paginate_by = 5

    def get_queryset(self):
        search_query = self.request.GET.get('search')
        tasks = super().get_queryset().filter(
            status="in_progress",
            ).order_by('priority')
        if search_query:
            tasks = tasks.filter(title__icontains=search_query)
        return tasks

class GenericCancelledListView(AuthorizedUserMixin, ListView):
    template_name = 'tasks.html'
    context_object_name = 'tasks'
    paginate_by = 5

    def get_queryset(self):
        search_query = self.request.GET.get('search')
        tasks = super().get_queryset().filter(
            status="cancelled",
            ).order_by('priority')
        if search_query:
            tasks = tasks.filter(title__icontains=search_query)
        return tasks

# view all tasks and completed tasks


class GenericAllTaskView(AuthorizedUserMixin, ListView):
    template_name = 'tasks.html'
    context_object_name = 'tasks'
    paginate_by = 5

    def get_queryset(self):
        search_query = self.request.GET.get('search')
        tasks = super().get_queryset().order_by('priority')
        if search_query:
            tasks = tasks.filter(title__icontains=search_query)
        return tasks


# Create a form view to receive time from the user for daily report
class ReportTimeForm(ModelForm):
    class Meta:
        model = Report
        fields = ['time', 'consent']


class CreateTimeView(AuthorizedUserMixin, UpdateView):
    form_class = ReportTimeForm
    template_name = 'reports.html'

    def get_form(self):
        form = super(CreateTimeView, self).get_form()
        form.fields['consent'].widget.attrs.update(
            {'class': SignUpView.checkboxCssClass})
        return form

    def get_object(self):
        return Report.objects.get_or_create(user=self.request.user)[0]
