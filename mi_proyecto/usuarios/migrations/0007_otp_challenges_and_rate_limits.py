from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('usuarios', '0006_cliente_bloqueado_hasta_cliente_intentos_fallidos')]

    operations = [
        migrations.CreateModel(
            name='OtpChallenge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(db_index=True, max_length=254)),
                ('pin_hash', models.CharField(max_length=128)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('consumed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={'indexes': [models.Index(fields=['email', 'consumed_at', 'created_at'], name='usuarios_ot_email_8e409d_idx')]},
        ),
        migrations.CreateModel(
            name='OtpRateLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kind', models.CharField(choices=[('email', 'Email'), ('ip', 'IP')], max_length=8)),
                ('subject_hash', models.CharField(max_length=64)),
                ('window_started_at', models.DateTimeField()),
                ('last_requested_at', models.DateTimeField()),
                ('requests_count', models.PositiveSmallIntegerField(default=0)),
            ],
            options={'constraints': [models.UniqueConstraint(fields=('kind', 'subject_hash'), name='uniq_otp_rate_subject')]},
        ),
    ]
