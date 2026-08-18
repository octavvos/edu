import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assignments', '0004_homework_per_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='homework',
            name='presentation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='courses.fileasset'),
        ),
    ]
