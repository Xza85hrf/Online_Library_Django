# Generated by Django 5.1.5 on 2025-05-25 20:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("library", "0002_librarysettings_bookloan_late_fee_paid_latefee_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="book",
            name="cover",
            field=models.ImageField(blank=True, null=True, upload_to="covers/"),
        ),
    ]
