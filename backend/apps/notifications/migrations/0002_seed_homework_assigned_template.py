from django.db import migrations


def seed_template(apps, schema_editor):
    NotificationTemplate = apps.get_model("notifications", "NotificationTemplate")
    NotificationTemplate.objects.get_or_create(
        event="homework_assigned", channel="in_app",
        defaults={"subject": {}, "body": {"uz": "Sizga yangi vazifa yuborildi"}, "is_active": True},
    )


def unseed_template(apps, schema_editor):
    NotificationTemplate = apps.get_model("notifications", "NotificationTemplate")
    NotificationTemplate.objects.filter(event="homework_assigned", channel="in_app").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_template, unseed_template),
    ]
