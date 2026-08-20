from django.db import migrations


def seed_template(apps, schema_editor):
    NotificationTemplate = apps.get_model("notifications", "NotificationTemplate")
    NotificationTemplate.objects.get_or_create(
        event="test_assigned", channel="in_app",
        defaults={"subject": {}, "body": {"uz": "Sizga yangi test yuborildi"}, "is_active": True},
    )


def unseed_template(apps, schema_editor):
    NotificationTemplate = apps.get_model("notifications", "NotificationTemplate")
    NotificationTemplate.objects.filter(event="test_assigned", channel="in_app").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("notifications", "0004_alter_notificationdispatch_event_and_more"),
    ]

    operations = [
        migrations.RunPython(seed_template, unseed_template),
    ]
