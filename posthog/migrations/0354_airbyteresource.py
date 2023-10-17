# Generated by Django 3.2.19 on 2023-09-19 14:19

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import posthog.models.utils


class Migration(migrations.Migration):

    dependencies = [
        ("posthog", "0353_add_5_minute_interval_to_batch_exports"),
    ]

    operations = [
        migrations.CreateModel(
            name="AirbyteResource",
            fields=[
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "id",
                    models.UUIDField(
                        default=posthog.models.utils.UUIDT, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("source_id", models.CharField(max_length=400)),
                ("connection_id", models.CharField(max_length=400)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                    ),
                ),
                ("status", models.CharField(max_length=400)),
                ("team", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="posthog.team")),
                ("source_type", models.CharField(choices=[("Stripe", "Stripe")], max_length=128)),
                ("are_tables_created", models.BooleanField(default=False)),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
