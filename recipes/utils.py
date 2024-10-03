import requests

import os
from dotenv import load_dotenv


# Load environment variables from .env file
load_dotenv()


def get_recipes(ingredients):
    api_key = os.getenv('api_key')
    # ad84aa46578048c79f4c971e87ad63b0
    # cedff321ed174072968bfcab9e525d2f
    #808e3031dfb94e788ebfe71786c9749d
    # Step 1: Find recipes by ingredients
    url_find = 'https://api.spoonacular.com/recipes/findByIngredients'
    params_find = {
        'ingredients': ','.join(ingredients),
        'number': 10,
        'apiKey': api_key
    }
    
    response_find = requests.get(url_find, params=params_find)
    
    if response_find.status_code != 200:
        return []  # Return an empty list if the request fails
    
    recipes = response_find.json()
    
    # Step 2: Get detailed information for each recipe
    detailed_recipes = []
    for recipe in recipes:
        recipe_id = recipe['id']
        url_info = f'https://api.spoonacular.com/recipes/{recipe_id}/information'
        params_info = {
            'apiKey': api_key
        }
        
        response_info = requests.get(url_info, params=params_info)
        
        if response_info.status_code == 200:
            detailed_recipes.append(response_info.json())

    return detailed_recipes
