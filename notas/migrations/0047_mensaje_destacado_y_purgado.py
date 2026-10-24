from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notas", "0046_colegio_mensajeria"),
    ]

    operations = [
        migrations.AddField(model_name="mensaje", name="destacado_por_remitente",
                            field=models.BooleanField(default=False)),
        migrations.AddField(model_name="mensaje", name="destacado_por_destinatario",
                            field=models.BooleanField(default=False)),
        migrations.AddField(model_name="mensaje", name="purgado_por_remitente",
                            field=models.BooleanField(default=False)),
        migrations.AddField(model_name="mensaje", name="purgado_por_destinatario",
                            field=models.BooleanField(default=False)),
    ]
