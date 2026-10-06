from django.db import models


class User(models.Model):
    email = models.EmailField()
    voice_embedding = models.BinaryField()