# Generated by Django 4.0.6 on 2022-08-09 07:57

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0033_remove_project_invitation"),
    ]

    operations = [
        migrations.AlterField(
            model_name="workspace",
            name="created_by",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="workspaces",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
