from django.urls import path
from . import views
from directory import views as d_views

urlpatterns = [
    path('menu', views.menu),
    path('researches', views.researches),
    path('researches-paraclinic', views.researches_paraclinic),
    path('researches/tune', views.researches_tune),
    path('researches/tune-ng', views.researches_tune_ng),
    path('researches/get_details', d_views.researches_get_details),
    path('tubes', views.tubes),
    path('directions_group', views.directions_group),
    path('uets', views.uets),
    path('with', views.onlywith),
    path('refs', views.refs),
    path('consults', views.construct_consults),
    path('templates', views.construct_templates),
    path('bacteria', views.construct_bacteria),
    path('dplan', views.construct_dispensary_plan),
]
