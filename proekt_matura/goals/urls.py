from django.urls import path
from . import views

app_name = 'goals'

urlpatterns = [
    path('',                          views.index,       name='index'),
    path('add/',                      views.add_goal,    name='add'),
    path('<uuid:pk>/contribute/',     views.contribute,  name='contribute'),
    path('<uuid:pk>/edit/',           views.edit_goal,   name='edit'),
    path('<uuid:pk>/delete/',         views.delete_goal, name='delete'),
]
