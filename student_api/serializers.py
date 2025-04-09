from rest_framework import serializers
from django.contrib.auth.models import User


from student_api.models import Students, SearchRecord


class StudentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Students
        fields = ['id', 'name', 'image_path', 'scan_id','created_at','identifier']


class SearchRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)

    class Meta:
        model = SearchRecord
        fields = ['id', 'search_image_path', 'scan_id', 'student', 'student_name', 'created_at']


