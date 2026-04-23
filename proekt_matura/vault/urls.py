from django.urls import path
from . import views

app_name = 'vault'

urlpatterns = [
    path('',                          views.index,          name='index'),
    path('add/',                      views.add_account,    name='add'),
    path('account/<int:pk>/edit/',   views.edit_account,   name='account_edit'),
    path('account/<int:pk>/delete/', views.delete_account, name='account_delete'),
    path('transfer/',                  views.transfer,       name='transfer'),
]
