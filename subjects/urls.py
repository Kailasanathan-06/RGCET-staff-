from django.urls import path
from . import views

app_name = 'subjects'

urlpatterns = [
    path('', views.SubjectListView.as_view(), name='list'),
    path('add/', views.SubjectCreateView.as_view(), name='add'),
    path('add-course/', views.CourseCreateView.as_view(), name='add_course'),
    path('<int:pk>/edit/', views.SubjectUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', views.SubjectDeleteView.as_view(), name='delete'),
]
