from django.contrib import admin

from flexible.imports import CSVFileImport


@admin.register(CSVFileImport)
class CSVFileImportAdmin(admin.ModelAdmin):
    pass
