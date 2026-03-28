from django.urls import path
from . import views

app_name = 'invest'

urlpatterns = [
    path('',                                  views.index,        name='index'),
    path('buy/',                              views.buy,          name='buy'),
    path('deposit/',                          views.deposit,      name='deposit'),
    path('withdraw/',                         views.withdraw,     name='withdraw'),
    path('transactions/',                     views.transactions, name='transactions'),
    path('holding/<uuid:pk>/sell/',           views.sell,         name='sell'),
    path('security/<uuid:pk>/update-price/',  views.update_price, name='update_price'),
]
