from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import  search_image

from . import views

urlpatterns = [
                  path('upload/', views.upload_image, name='upload_image'),
                  path('upload/update/<int:id>/', views.update_image, name='update_image'),
                  path('search/', search_image, name='search_image'),
              ] + static(settings.MEDIA_URL,
                         document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)