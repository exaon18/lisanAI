from django.db import models

# Create your models here.
class User(models.Model):
    telegram_id = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    spoken_languages = models.CharField(max_length=255, blank=True, null=True)  # Comma-separated list of languages
    lang_to_learn = models.CharField(max_length=255, blank=True, null=True)  # Comma-separated list of languages
    last_login = models.DateTimeField(blank=True, null=True)
    userpic=models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return f"{self.first_name} ({self.telegram_id})"