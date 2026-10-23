from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("notas", "0045_catalogo_de_faltas"),
    ]

    operations = [
        migrations.AddField(
            model_name="colegio",
            name="whatsapp_automatico",
            field=models.BooleanField(
                default=False,
                help_text="Los avisos del observador salen solos por la línea de WhatsApp de la plataforma (cuando esté conectada). Si no, siguen saliendo con el botón de WhatsApp.",
                verbose_name="Avisos automáticos por WhatsApp",
            ),
        ),
        migrations.AddField(
            model_name="colegio",
            name="correo_remitente_verificado",
            field=models.BooleanField(
                default=False,
                help_text="Solo si el correo de contacto del colegio ya se verificó en el proveedor de correo de la plataforma. Si no, los correos salen con el nombre del colegio y las respuestas le llegan a ese correo.",
                verbose_name="Correos desde el correo del colegio",
            ),
        ),
    ]
