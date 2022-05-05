from django.db import models


class News(models.Model):

    header = models.CharField(max_length=256) # in HEX
    body = models.TextField() # in HEX
    image = models.TextField()
    # image = models.ImageField(upload_to='news/')

    class Meta:
        verbose_name_plural = "News"