from django.db import models


class CompilationRun(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    source = models.TextField()
    result_json = models.JSONField()


class Meta:
    ordering = ['-created_at']
