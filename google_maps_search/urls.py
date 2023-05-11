from django.urls import path
from . import views

urlpatterns = [
    path('', views.search, name='search'),
    path('download_csv/', views.download_csv, name='download_csv'),
]
