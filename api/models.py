from django.db import models


class Game(models.Model):
    app_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    release_date = models.DateField()
    required_age = models.IntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    dlc_count = models.IntegerField()
    about = models.TextField()
    supported_languages = models.TextField()
    windows = models.BooleanField()
    mac = models.BooleanField()
    linux = models.BooleanField()
    positive = models.IntegerField()
    negative = models.IntegerField()
    score_rank = models.CharField(max_length=50, null=True, blank=True)
    developers = models.CharField(max_length=255)
    publishers = models.TextField()
    categories = models.TextField()
    genres = models.TextField()
    tags = models.TextField()

    def __str__(self):
        return self.name
