"""
Data migration: remove Civil Engineering (CIVIL) subjects from the system.

CIVIL subjects (CE3301 Structural Analysis I, CE3402 Environmental Engineering)
were removed from the seed dataset. This migration deactivates any that already
exist and clears their teacher assignments.
"""
from django.db import migrations


def deactivate_civil_subjects(apps, schema_editor):
    Subject = apps.get_model('subjects', 'Subject')
    TeacherSubject = apps.get_model('subjects', 'TeacherSubject')

    civil_subjects = Subject.objects.filter(department__code='CIVIL')
    TeacherSubject.objects.filter(subject__in=civil_subjects).delete()
    civil_subjects.update(status='inactive')


def reverse_civil_subjects(apps, schema_editor):
    Subject = apps.get_model('subjects', 'Subject')
    Subject.objects.filter(department__code='CIVIL').update(status='active')


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(deactivate_civil_subjects, reverse_civil_subjects),
    ]
