# Generated by Django 3.2.5 on 2021-09-08 05:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='usertype',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
