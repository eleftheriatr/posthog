# Generated by Django 4.2.14 on 2024-08-09 09:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("posthog", "0452_organization_logo"),
    ]

    operations = [
        migrations.AddField(
            model_name="hogfunction",
            name="masking",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
