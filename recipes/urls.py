from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_recipes, name='search_recipes'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='recipes/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='recipes/logout.html'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('about/', views.about, name='about'),
    path('add-to-favorites/<int:recipe_id>/', views.add_to_favorites, name='add_to_favorites'),
    path('remove-from-favorites/<int:recipe_id>/', views.remove_from_favorites, name='remove_from_favorites'),
    path('favorites/', views.favorites, name='favorites'),
    path('visualizations/', views.ingredient_popularity_chart, name='visualizations'),
 
]
