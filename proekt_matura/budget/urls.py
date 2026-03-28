from django.urls import path
from . import views

app_name = 'budget'

urlpatterns = [
    path('',                        views.index,          name='index'),
    path('add/',                    views.add_entry,      name='add'),
    path('invest-now/',             views.invest_now,     name='invest_now'),
    path('category/add/',           views.add_category,   name='add_category'),
    path('entry/<int:pk>/edit/',   views.edit_entry,     name='entry_edit'),
    path('entry/<int:pk>/delete/', views.delete_entry,   name='entry_delete'),
]
