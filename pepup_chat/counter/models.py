from django.db import models


class FastCounter(models.Model):
    key = models.CharField(max_length=30, db_index=True, unique=True)
    count = models.IntegerField(default=0)
