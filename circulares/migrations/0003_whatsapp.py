from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("circulares", "0002_circular_para_personal"),
    ]

    operations = [
        migrations.AddField(
            model_name="circular",
            name="por_whatsapp",
            field=models.BooleanField(default=False, verbose_name="Avisar también por WhatsApp a las familias"),
        ),
        migrations.AddField(
            model_name="lectura",
            name="whatsapp_enviado",
            field=models.DateTimeField(blank=True, help_text="Cuándo salió el aviso por WhatsApp.", null=True),
        ),
        migrations.AddField(
            model_name="lectura",
            name="whatsapp_detalle",
            field=models.CharField(blank=True, help_text="A quién se le mandó o por qué no salió.", max_length=120),
        ),
    ]
