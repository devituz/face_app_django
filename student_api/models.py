from django.db import models

class Students(models.Model):
    name = models.CharField(max_length=255)
    identifier = models.CharField(max_length=255, null=True, blank=True)
    image_path = models.CharField(max_length=255)
    face_encoding = models.JSONField()
    scan_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



class SearchRecord(models.Model):
    search_image_path = models.CharField(max_length=255)
    scan_id = models.CharField(max_length=255, null=True, blank=True)
    student = models.ForeignKey(Students, on_delete=models.CASCADE, related_name='search_records', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.id} - {self.scan_id}"
