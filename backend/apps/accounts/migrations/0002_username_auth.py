"""
Username asosidagi autentifikatsiyaga o'tish.

USERNAME_FIELD "phone" -> "username" bo'ldi; qo'shimcha ism/familiya
maydonlari va "pending" (mentor tasdig'ini kutish) holati qo'shildi.

Mavjud qatorlar uchun username id'dan generatsiya qilinadi — bu maydon
unique bo'lgani uchun bo'sh satr bilan to'ldirib bo'lmaydi.
"""

from django.db import migrations, models

import apps.accounts.validators


def backfill_usernames(apps_registry, schema_editor):
    User = apps_registry.get_model("accounts", "User")
    for user in User.objects.filter(username=""):
        # id'ning birinchi 8 belgisi — noyob va validator qoidalariga mos
        User.objects.filter(pk=user.pk).update(username=f"user_{str(user.pk)[:8]}")


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="username",
            # Vaqtincha bo'sh satrga ruxsat beramiz, keyin backfill qilib
            # unique cheklovini qo'yamiz.
            field=models.CharField(default="", max_length=150),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="user",
            name="first_name",
            field=models.CharField(blank=True, max_length=75),
        ),
        migrations.AddField(
            model_name="user",
            name="last_name",
            field=models.CharField(blank=True, max_length=75),
        ),
        migrations.RunPython(backfill_usernames, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(
                help_text="Kamida 4 belgi: harf, raqam va _ . - belgilari",
                max_length=150,
                unique=True,
                validators=[apps.accounts.validators.UsernameValidator()],
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Mentor tasdig'i kutilmoqda"),
                    ("active", "Faol"),
                    ("blocked", "Bloklangan"),
                    ("pending_deletion", "O'chirish kutilmoqda"),
                    ("anonymized", "Anonimlashtirilgan"),
                ],
                default="active",
                max_length=20,
            ),
        ),
    ]
