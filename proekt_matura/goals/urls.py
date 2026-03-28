from django.urls import path
from . import views

app_name = 'goals'

urlpatterns = [
    path('',                          views.index,       name='index'),
    path('add/',                      views.add_goal,    name='add'),
    path('<int:pk>/contribute/',     views.contribute,  name='contribute'),
    path('<int:pk>/edit/',           views.edit_goal,   name='edit'),
    path('<int:pk>/delete/',         views.delete_goal, name='delete'),
]
