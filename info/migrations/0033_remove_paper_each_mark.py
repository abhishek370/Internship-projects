# Generated by Django 2.2.12 on 2022-11-29 11:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0032_auto_20221129_1103'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paper',
            name='each_mark',
        ),
    ]
