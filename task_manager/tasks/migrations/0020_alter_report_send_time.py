# Generated by Django 3.2.12 on 2022-04-19 04:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0019_auto_20220419_0453'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='send_time',
            field=models.DateTimeField(blank=True, default='2022-04-19 04:54:00', help_text='Enter UTC time in HH:MM'),
        ),
    ]
