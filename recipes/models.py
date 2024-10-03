from django.db import models
from django.contrib.auth.models import User

class Ingredient(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    ingredients = models.ManyToManyField(Ingredient)
    instructions = models.TextField()

    def __str__(self):
        return self.title

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe_id = models.IntegerField()
    recipe_title = models.CharField(max_length=255)
    recipe_image = models.URLField()
    ingredients = models.TextField()  # Use TextField for simplicity
    instructions = models.TextField(default="")
    cooking_time = models.IntegerField(default=0)  # Default to 0 minutes
    servings = models.IntegerField(default=1)  # Default to 1 serving
    health_score = models.IntegerField(default=0)  # Default to 0
    summary = models.TextField(default="")

    def __str__(self):
        return f"{self.user.username} - {self.recipe_title}"

class IngredientSearch(models.Model):
    ingredient_name = models.CharField(max_length=100, unique=True)
    search_count = models.IntegerField(default=0)

    def __str__(self):
        return self.ingredient_name