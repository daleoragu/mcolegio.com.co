# notas/forms/portal_forms.py
from django import forms
# Se importan todos los modelos necesarios desde su ubicación correcta
from ..models import DocumentoPublico, FotoGaleria, Noticia, ImagenCarrusel, Colegio

class DocumentoPublicoForm(forms.ModelForm):
    class Meta:
        model = DocumentoPublico
        fields = ['titulo', 'descripcion', 'archivo']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
        }

class FotoGaleriaForm(forms.ModelForm):
    class Meta:
        model = FotoGaleria
        fields = ['titulo', 'imagen']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['titulo', 'resumen', 'cuerpo', 'imagen_portada', 'estado']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'resumen': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'cuerpo': forms.Textarea(attrs={'class': 'form-control', 'rows': 10}),
            'imagen_portada': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

class ImagenCarruselForm(forms.ModelForm):
    class Meta:
        model = ImagenCarrusel
        fields = ['titulo', 'subtitulo', 'imagen', 'orden', 'visible']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control'}),
            'subtitulo': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
            'visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# --- INICIO: FORMULARIO DEFINITIVO Y CORREGIDO ---
class ColegioPersonalizacionForm(forms.ModelForm):
    class Meta:
        model = Colegio
        fields = [
            'nombre', 'lema',
            'historia', 'mision', 'vision', 'modelo_pedagogico',
            'escudo', 'favicon',
            'color_primario', 'color_texto_primario', 'color_secundario', 'color_fondo', 
            'color_topbar', 'color_topbar_texto', 'color_footer', 'color_footer_texto',
            'telefono', 'email_contacto', 'whatsapp_numero',
            'url_facebook', 'url_instagram', 'url_tiktok', 'url_youtube',
            'layout_portal', 
            'portal_publico_activo'
        ]
        widgets = {
            # --- Textos y Contenidos ---
            # --- LÍNEA CORREGIDA ---
            # Se añade 'readonly': True para que el campo no sea editable pero su valor se envíe.
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'readonly': True}),
            'lema': forms.TextInput(attrs={'class': 'form-control'}),
            'historia': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'mision': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'vision': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'modelo_pedagogico': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            
            # --- Imágenes y Logos ---
            'escudo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'favicon': forms.ClearableFileInput(attrs={'class': 'form-control'}),

            # --- Paleta de Colores ---
            'color_primario': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_texto_primario': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_secundario': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_fondo': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_topbar': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_topbar_texto': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_footer': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),
            'color_footer_texto': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'}),

            # --- Contacto y Redes Sociales ---
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email_contacto': forms.EmailInput(attrs={'class': 'form-control'}),
            'whatsapp_numero': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 573001234567'}),
            'url_facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'url_instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'url_tiktok': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://www.tiktok.com/@sucolegio'}),
            'url_youtube': forms.URLInput(attrs={'class': 'form-control'}),

            # --- Configuración ---
            'layout_portal': forms.Select(attrs={'class': 'form-select'}),
            'portal_publico_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        help_texts = {
            'portal_publico_activo': "Marcar si desea que el portal sea visible para todos.",
            'escudo': "Logo principal que aparecerá en el portal.",
            'favicon': "Icono pequeño para la pestaña del navegador (ej: 32x32px)."
        }
# --- FIN: FORMULARIO DEFINITIVO Y CORREGIDO ---
