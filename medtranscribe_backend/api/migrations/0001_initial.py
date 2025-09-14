"""
Initial migration for MMT custom tables that work with OpenEMR database.
Only creates tables that are not managed by OpenEMR.
"""

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        # Create custom transcription tables (not managed by OpenEMR)
        migrations.CreateModel(
            name='Transcription',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('filename', models.CharField(max_length=255)),
                ('original_filename', models.CharField(max_length=255)),
                ('file_size', models.IntegerField()),
                ('duration_seconds', models.IntegerField(blank=True, null=True)),
                ('transcription_text', models.TextField()),
                ('confidence_score', models.FloatField(blank=True, null=True)),
                ('language_detected', models.CharField(default='en', max_length=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('completed', 'Completed'), ('failed', 'Failed'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('processed_at', models.DateTimeField(blank=True, null=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('openemr_note_id', models.IntegerField(blank=True, null=True)),
                ('integrated_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'db_table': 'mmt_transcriptions',
                'ordering': ['-created_at'],
            },
        ),
        
        migrations.CreateModel(
            name='TranscriptionSegment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('segment_number', models.IntegerField()),
                ('start_time', models.FloatField(blank=True, null=True)),
                ('end_time', models.FloatField(blank=True, null=True)),
                ('text', models.TextField()),
                ('confidence_score', models.FloatField(blank=True, null=True)),
                ('edited', models.BooleanField(default=False)),
                ('edited_at', models.DateTimeField(blank=True, null=True)),
                ('transcription', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='segments', to='api.transcription')),
            ],
            options={
                'db_table': 'mmt_transcription_segments',
                'ordering': ['segment_number'],
            },
        ),
    ]