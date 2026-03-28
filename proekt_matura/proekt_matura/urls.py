from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from users import views as user_views
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', core_views.home, name='home'),

    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', user_views.register, name='signup'),
    path('register/', user_views.register, name='register'),

    path('dashboard/', user_views.dashboard, name='dashboard'),
    path('profile/', user_views.profile, name='profile'),

    path('vault/', include('vault.urls', namespace='vault')),
    path('budget/', include('budget.urls', namespace='budget')),
    path('invest/', include('invest.urls', namespace='invest')),
    path('goals/', include('goals.urls', namespace='goals')),

]