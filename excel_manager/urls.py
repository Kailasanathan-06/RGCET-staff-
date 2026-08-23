from django.urls import path
from . import views

app_name = 'excel_manager'

urlpatterns = [
    path('import/', views.ExcelUploadView.as_view(), name='import'),
    path('import/<int:pk>/map/', views.ExcelMapAndProcessView.as_view(), name='map'),
]
