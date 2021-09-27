# Generated by Django 3.2.5 on 2021-09-22 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("applications", "0002_application_has_reached_confirmation"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="researcherregistration",
            name="github_username",
        ),
        migrations.AddField(
            model_name="researcherregistration",
            name="does_researcher_need_server_access",
            field=models.BooleanField(
                choices=[(True, "Yes"), (False, "No")], null=True
            ),
        ),
        migrations.AlterField(
            model_name="researcherregistration",
            name="has_taken_safe_researcher_training",
            field=models.BooleanField(
                choices=[(True, "Yes"), (False, "No")], null=True
            ),
        ),
        migrations.AlterField(
            model_name="researcherregistration",
            name="phone_type",
            field=models.TextField(
                blank=True,
                choices=[("android", "Android"), ("iphone", "iPhone")],
                default="",
            ),
        ),
        migrations.AlterField(
            model_name="researcherregistration",
            name="telephone",
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name="researcherregistration",
            name="training_passed_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="researcherregistration",
            name="training_with_org",
            field=models.TextField(blank=True),
        ),
    ]
