from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('', views.reservation_list, name='list'),
    path('search/', views.reservation_search, name='search'),
    path('create/', views.reservation_create, name='create'),
    path('<int:pk>/', views.reservation_detail, name='detail'),
    path('<int:pk>/update/', views.reservation_update, name='update'),
    path('<int:pk>/delete/', views.reservation_delete, name='delete'),
    path('export/excel/', views.export_reservations_excel, name='export_excel'),
    path('export/pdf/', views.export_reservations_pdf, name='export_pdf'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('financial-debug/', views.financial_debug, name='financial_debug'),
    path('recalculate-margins/', views.recalculate_margins, name='recalculate_margins'),
    # ELIMINADA: path('dashboard/export-pdf/', views.export_dashboard_pdf, name='export_dashboard_pdf'),
    path('dashboard/export-excel/', views.export_dashboard_excel, name='export_dashboard_excel'),
    path('backup/', views.backup_management, name='backup_management'),
    path('backup/download/', views.backup_download, name='backup_download'),
    path('backup/restore/', views.backup_restore, name='backup_restore'),
    path('importar/', views.importar_menu, name='importar_menu'),
    path('importar/paximum/', views.importar_paximum, name='importar_paximum'),
    path('importar/bedbankglobal/', views.importar_bedbankglobal, name='importar_bedbankglobal'),
]