from django.shortcuts import render, redirect, get_object_or_404
from .models import Ingredient, Favorite, Recipe, IngredientSearch
from .utils import get_recipes
from django.contrib import messages
from .forms import UserRegisterForm, UpdateProfileForm, CustomPasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
import json
import requests
from django.conf import settings
from django.http import JsonResponse
from django.http import Http404
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import ast



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        print(f"Username: {username}, Password: {password}")  # Debugging

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')  # Redirect to dashboard or desired page after successful login
        else:
            messages.error(request, "Invalid username or password")
    
    return render(request, 'login.html')


def home(request):
    return render(request, 'recipes/home.html')

@login_required
def search_recipes(request):
    if request.method == 'POST':
        ingredients_input = request.POST.get('ingredient', '').strip()
        if not ingredients_input:
            messages.error(request, 'Please enter at least one ingredient.')
            return render(request, 'recipes/search.html')
        
        ingredient_names = [ingredient.strip() for ingredient in ingredients_input.split(',')]
         # Update search count for each ingredient
        for ingredient_name in ingredient_names:
            ingredient_search, created = IngredientSearch.objects.get_or_create(ingredient_name=ingredient_name)
            ingredient_search.search_count += 1
            ingredient_search.save()


        recipes = get_recipes(ingredient_names)

        # Get the user's current favorite recipes
        user_favorites = Favorite.objects.filter(user=request.user).values_list('recipe_id', flat=True)
        
        return render(request, 'recipes/results.html', {
            'recipes': recipes,
            'user_favorites': user_favorites
        })
    
    return render(request, 'recipes/search.html')


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically login the user after registration
            messages.success(request, f'Account created for {user.username}!')
            return redirect('home')  # Redirect to home or any other page
    else:
        form = UserRegisterForm()
    return render(request, 'recipes/register.html', {'form': form})

@login_required
def dashboard(request):
    user = request.user
    favorite_recipes = Favorite.objects.filter(user=user)
    return render(request, 'recipes/dashboard.html', {'favorites': favorite_recipes})

@login_required
def profile_view(request):
    if request.method == 'POST':
        # Check which form is being submitted
        if 'update_profile' in request.POST:
            profile_form = UpdateProfileForm(request.POST, instance=request.user)
            password_form = CustomPasswordChangeForm(request.user)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Profile updated successfully!')
                return redirect('profile')

        elif 'change_password' in request.POST:
            profile_form = UpdateProfileForm(instance=request.user)
            password_form = CustomPasswordChangeForm(request.user, request.POST)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep the user logged in after password change
                messages.success(request, 'Password changed successfully!')
                return redirect('profile')
            else:
                messages.error(request, 'Error changing your password.')

    else:
        profile_form = UpdateProfileForm(instance=request.user)
        password_form = CustomPasswordChangeForm(request.user)

    return render(request, 'recipes/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
    })



def about(request):
    return render(request, 'recipes/about.html')

@login_required
@require_POST
def add_to_favorites(request, recipe_id):
    if Favorite.objects.filter(user=request.user, recipe_id=recipe_id).exists():
        messages.info(request, 'Recipe is already in your favorites.')
        return redirect('favorites')

    # Get the recipe details from the POST request
    recipe_title = request.POST.get('recipe_title')
    recipe_image = request.POST.get('recipe_image')
    ingredients = request.POST.get('ingredients')
    instructions = request.POST.get('instructions')
    cooking_time = request.POST.get('cooking_time')
    servings = request.POST.get('servings')
    health_score = request.POST.get('health_score')
    summary = request.POST.get('summary')

    try:
        # Create and save the Favorite object
        favorite = Favorite(
            user=request.user,
            recipe_id=recipe_id,
            recipe_title=recipe_title,
            recipe_image=recipe_image,
            ingredients=ingredients,
            instructions=instructions,
            cooking_time=int(cooking_time),
            servings=int(servings),
            health_score=int(health_score),
            summary=summary
        )
        favorite.save()
        messages.success(request, 'Recipe added to your favorites!')
    except ValueError as e:
        messages.error(request, f'There was an error processing the recipe data: {str(e)}')

    return redirect('favorites')

@login_required
@require_POST
def remove_from_favorites(request, recipe_id):
    # Check if the recipe is in the user's favorites
    favorite = Favorite.objects.filter(user=request.user, recipe_id=recipe_id).first()
    if favorite:
        favorite.delete()
        messages.success(request, 'Recipe removed from favorites successfully.')
    else:
        messages.error(request, 'Recipe not found in your favorites.')
    
    return redirect('favorites')

@login_required
def favorites(request):
    user = request.user
    favorites = user.favorite_set.all()

    # Process ingredients for each favorite
    for favorite in favorites:
        try:
            favorite.ingredients_list = ast.literal_eval(favorite.ingredients)
        except (ValueError, SyntaxError):
            favorite.ingredients_list = []

    return render(request, 'recipes/favorites.html', {'favorites': favorites})



import json
from django.db import models


@login_required
def ingredient_popularity_chart(request):
    # Get the top 10 most searched ingredients
    top_ingredients = IngredientSearch.objects.order_by('-search_count')[:50]

    ingredient_names = [ingredient.ingredient_name for ingredient in top_ingredients]
    search_counts = [ingredient.search_count for ingredient in top_ingredients]


    # Get the top 10 most popular recipes
    top_recipes = Favorite.objects.values('recipe_title').annotate(favorite_count=models.Count('id')).order_by('-favorite_count')[:10]
    recipe_titles = [recipe['recipe_title'] for recipe in top_recipes]
    favorite_counts = [recipe['favorite_count'] for recipe in top_recipes]


     # Get health scores for favorited recipes
    health_scores_raw = Favorite.objects.values_list('health_score', flat=True)
    health_scores_bins = [0] * 10  # Initialize 10 bins for the histogram

    for score in health_scores_raw:
        bin_index = min(score // 10, 9)  # Ensure the score falls into the correct bin
        health_scores_bins[bin_index] += 1


    return render(request, 'recipes/visualizations.html', {
        'ingredient_names': json.dumps(ingredient_names),  # Send data as JSON to JavaScript
        'search_counts': json.dumps(search_counts),
        'recipe_titles': json.dumps(recipe_titles),  # Send data as JSON to JavaScript
        'favorite_counts': json.dumps(favorite_counts),
        'health_scores': json.dumps(health_scores_bins),  # Send histogram data as JSON to JavaScript
    })
