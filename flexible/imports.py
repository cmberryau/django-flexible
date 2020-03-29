from django.db import models


class CSVFileImport(models.Model):
    csv_file = models.FileField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "CSV File Imports"

    def __str__(self):
        return f"{self.csv_file} @ {self.created}"
