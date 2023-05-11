from django.db import models

# Create your models here.
from django.db import models

class SearchResult(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    latitude = models.FloatField()
    longitude = models.FloatField()
    rating = models.FloatField(null=True, blank=True)
    distance = models.IntegerField()

    def __str__(self):
        return self.name
