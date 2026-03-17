from django.urls import path

from . import views

app_name = 'nutrition'

urlpatterns = [
    path('', views.calculator_view, name='calculator'),
    path('calculate/', views.calculate_api, name='calculate'),
]
