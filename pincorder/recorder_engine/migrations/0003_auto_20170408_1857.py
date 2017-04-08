# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-08 16:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('recorder_engine', '0002_auto_20170408_1405'),
    ]

    operations = [
        migrations.AlterField(
            model_name='course',
            name='teacher',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='recorder_engine.Teacher'),
        ),
        migrations.AlterField(
            model_name='pin',
            name='media_url',
            field=models.FileField(blank=True, upload_to='raw_upload/'),
        ),
        migrations.AlterField(
            model_name='recordingfile',
            name='file_url',
            field=models.FileField(upload_to='raw_upload/'),
        ),
    ]
