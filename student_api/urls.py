from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import upload_image, update_image, search_image,allsearch, get_user_images, getme_register
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
                  path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
                  path('upload/', views.upload_image, name='upload_image'),
                  path('upload/update/<int:id>/', views.update_image, name='update_image'),
                  path('search/', search_image, name='search_image'),
                  path('all/', views.allsearch, name='all'),
                  path('getme_register/', getme_register, name='getme_register'),
                  path('candidates/delete/', views.delete_candidate_records, name='delete_candidate_records'),
                  path('user_images/', views.get_user_images, name='get_user_images'),
                  path('user_json/', views.get_user_json, name='get_user_json'),
                  path('search_user_json/', views.search_user_json, name='search_user_json'),
                  path('user_delete/', views.delete_records_by_id, name='user_delete'),
              ] + static(settings.MEDIA_URL,
                         document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)