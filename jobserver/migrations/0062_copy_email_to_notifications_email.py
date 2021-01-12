# Generated by Django 3.1.2 on 2021-01-12 15:47

from django.db import migrations
from django.db.models import F


def copy_email_to_notifications_email(apps, schema_editor):
    User = apps.get_model("jobserver", "User")

    User.objects.update(notifications_email=F("email"))


def remove_notifications_email(apps, schema_editor):
    User = apps.get_model("jobserver", "User")

    User.objects.update(notifications_email="")


class Migration(migrations.Migration):

    dependencies = [
        ("jobserver", "0061_add_user_notification_email"),
    ]

    operations = [
        migrations.RunPython(
            copy_email_to_notifications_email, reverse_code=remove_notifications_email
        )
    ]
