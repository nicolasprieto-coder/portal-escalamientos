from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('incidencias.urls')),
    path('catalogo/', include('catalogo.urls')),
]