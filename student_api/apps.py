from django.apps import AppConfig


class StudentApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'student_api'

    def ready(self):
        # Ilova ishga tushganda `process_and_save_student_images` funksiyasini chaqirishdi
        from .utils import process_and_save_student_images
        process_and_save_student_images()