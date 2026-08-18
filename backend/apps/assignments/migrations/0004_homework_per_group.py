"""
Vazifa endi guruhga jo'natiladi: (dars, guruh) juftligi kaliti.

Bitta kursni bir necha guruh baham ko'rgani uchun avvalgi 1:1 (dars ->
vazifa) modeli vazifani hamma guruhga birdan ko'rsatardi. Qo'lda yozilgan,
chunki `group` majburiy FK — makemigrations interaktiv default so'raydi.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assignments", "0003_homework_material"),
        ("groups", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="homework",
            name="lesson",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="homeworks",
                to="courses.lesson",
            ),
        ),
        migrations.AddField(
            model_name="homework",
            name="group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="homeworks",
                to="groups.group",
                # Mavjud yozuv yo'q (jo'natish funksiyasi shu relizda qo'shildi),
                # shuning uchun ma'lumot migratsiyasi kerak emas.
                default=None,
                null=False,
            ),
            preserve_default=False,
        ),
        migrations.AddConstraint(
            model_name="homework",
            constraint=models.UniqueConstraint(
                fields=("lesson", "group"), name="uniq_homework_per_lesson_group",
            ),
        ),
        migrations.AddIndex(
            model_name="homework",
            index=models.Index(fields=["group"], name="assignments_group_i_32e3d2_idx"),
        ),
    ]
