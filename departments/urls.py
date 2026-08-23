from django.urls import path
from . import views

app_name = 'departments'

urlpatterns = [
    path('', views.DepartmentListView.as_view(), name='list'),
    path('add/', views.DepartmentCreateView.as_view(), name='add'),
    path('<int:pk>/edit/', views.DepartmentUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.DepartmentDeleteView.as_view(), name='delete'),
]
