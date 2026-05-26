from django.urls import path
from . import views

urlpatterns = [
    path('',                        views.lista_servicios,  name='lista_servicios'),
    path('nuevo/',                  views.crear_servicio,   name='crear_servicio'),
    path('editar/<int:pk>/',        views.editar_servicio,  name='editar_servicio'),
    path('eliminar/<int:pk>/',      views.eliminar_servicio,name='eliminar_servicio'),
]