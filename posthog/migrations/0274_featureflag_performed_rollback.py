# Generated by Django 3.2.15 on 2022-10-20 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("posthog", "0273_auto_20221020_1507"),
    ]

    operations = [
        migrations.AddField(
            model_name="featureflag",
            name="performed_rollback",
            field=models.BooleanField(default=False, null=True),
        ),
    ]
