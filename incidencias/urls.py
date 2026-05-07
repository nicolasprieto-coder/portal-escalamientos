from django.urls import path
from . import views

urlpatterns = [
    path('',                         views.dashboard,          name='dashboard'),
    path('inicio/',                  views.inicio,             name='inicio'),
    path('registrar/',               views.registrar,          name='registrar'),
    path('previsualizar/<int:pk>/',  views.previsualizar,      name='previsualizar'),
    path('historial/',               views.historial,          name='historial'),
    path('detalle/<int:pk>/',        views.detalle,            name='detalle'),
    path('cerrar/<int:pk>/',         views.cerrar_escalamiento,name='cerrar'),
    path('eliminar/<int:pk>/',       views.eliminar,           name='eliminar'),
    path('api/servicio/<str:sid>/',  views.info_servicio,      name='info_servicio'),
    path('api/check-respuestas/',    views.check_respuestas,   name='check_respuestas'),
]