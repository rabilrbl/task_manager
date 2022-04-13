# Generated by Django 3.2.12 on 2022-04-13 11:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0008_alter_report_send_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='send_time',
            field=models.DateTimeField(blank=True, default='2022-04-13 11:49:00', help_text='Enter UTC time in HH:MM'),
        ),
        migrations.CreateModel(
            name='Board',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, max_length=500)),
                ('tasks', models.ManyToManyField(blank=True, to='tasks.Task')),
            ],
        ),
    ]
