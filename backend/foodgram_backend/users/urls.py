from django.urls import path, include
from djoser.views import UserViewSet
from djoser.urls.base import urlpatterns as users_urls

app_name = 'users'

urlpatterns = [
    path('', include(users_urls)),
]
