# Generated by Django 3.1.2 on 2021-03-08 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0014_release"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_approved",
            field=models.BooleanField(default=False),
        ),
    ]
