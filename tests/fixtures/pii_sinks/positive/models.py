from django.db import models


class User(models.Model):
    """Usuario con datos personales de contacto y voz (STT)."""
    email = models.EmailField()
    voice_embedding = models.BinaryField()