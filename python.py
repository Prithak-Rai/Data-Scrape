import requests
import json

def get_google_reviews_by_pid(place_id, api_key):
    # Define the SerpAPI endpoint for Google Reviews
    search_url = 'https://serpapi.com/search'
    
    # Parameters for the request using Place ID
    params = {
        'place_id': place_id,
        'api_key': api_key,
        'engine': 'google_maps_reviews'
    }

    # Sending request to SerpAPI to get reviews for the given Place ID
    response = requests.get(search_url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        # Extracting reviews and ratings
        try:
            reviews = data['reviews']
            for review in reviews:
                user_name = review.get('user_name', 'N/A')
                rating = review.get('rating', 'N/A')
                comment = review.get('comment', 'N/A')
                food_rating = review.get('food_rating', 'N/A')
                service_rating = review.get('service_rating', 'N/A')
                atmosphere_rating = review.get('atmosphere_rating', 'N/A')
                
                print(f"User: {user_name}")
                print(f"Rating: {rating}")
                print(f"Comment: {comment}")
                print(f"Food Rating: {food_rating}")
                print(f"Service Rating: {service_rating}")
                print(f"Atmosphere Rating: {atmosphere_rating}")
                print("-" * 40)
        except KeyError:
            print("Error: Could not find reviews in the data.")
    else:
        print(f"Error: {response.status_code}, could not fetch data.")

# Replace with your SerpAPI key and the Place ID
api_key = 'e48ed22679110ff8bdb0c2b547bf4808f15bc5685127eff10538d1efcee8867f'
place_id = 'ChIJwwuPrOMbdkgRmR25bt1SMLU'  # Replace with the Place ID of the restaurant

get_google_reviews_by_pid(place_id, api_key)
