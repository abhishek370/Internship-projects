# Generated by Django 2.2.12 on 2022-11-23 08:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0019_auto_20221123_0729'),
    ]

    operations = [
        migrations.AddField(
            model_name='addexam',
            name='exam_name',
            field=models.CharField(max_length=100, null=True),
        ),
    ]
