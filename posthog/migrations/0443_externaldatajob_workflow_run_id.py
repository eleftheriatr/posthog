# Generated by Django 4.2.11 on 2024-07-16 20:29

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("posthog", "0442_alter_survey_questions"),
    ]

    operations = [
        migrations.AddField(
            model_name="externaldatajob",
            name="workflow_run_id",
            field=models.CharField(blank=True, max_length=400, null=True),
        ),
    ]
