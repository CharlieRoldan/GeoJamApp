from django.urls import path
from django.views.generic import TemplateView
from django.contrib import admin
from django.urls import include, path


urlpatterns = [
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('admin/', admin.site.urls),
    path('google_maps_search/', include('google_maps_search.urls')),
]
