# Generated by Django 2.2.12 on 2022-12-08 15:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('info', '0039_class_fees'),
    ]

    operations = [
        migrations.AddField(
            model_name='class',
            name='month',
            field=models.IntegerField(blank=True, default=12, null=True),
        ),
    ]
