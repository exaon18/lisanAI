import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import User

# Create your views here.
@csrf_exempt
def index(request):
    # Dev-friendly logging + CORS handling (use a dedicated CORS setup for production).
    origin = request.headers.get('Origin')

    if request.method == 'OPTIONS':
        response = JsonResponse({'status': 'ok'})
        if origin:
            response['Access-Control-Allow-Origin'] = origin
            response['Vary'] = 'Origin'
        response['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    if request.method == 'POST':
        try:
            print('[lisan] POST / origin=', origin)
            data = json.loads(request.body or b'{}')
            # You can now access your data like this:
            # telegram_id = data.get('telegram_id')
            # first_name = data.get('first_name')
            # ...
            print(data)  # For debugging purposes, print the parsed data
            # Create a new User instance
            
            telegram_id = data.get('telegram_id')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            username = data.get('username')
            spoken_languages = data.get('spoken_language')
            lang_to_learn = data.get('language_to_learn')
            created,user= User.objects.get_or_create(
                telegram_id=telegram_id,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'username': username,
                    'spoken_languages': spoken_languages,
                    'lang_to_learn': lang_to_learn
                }
            )
            response = JsonResponse({'status': 'success', 'message': 'Data received'})
            if origin:
                response['Access-Control-Allow-Origin'] = origin
                response['Vary'] = 'Origin'
            return response
        except json.JSONDecodeError:
            response = JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
            if origin:
                response['Access-Control-Allow-Origin'] = origin
                response['Vary'] = 'Origin'
            return response
    
    response = render(request, 'index.html')
    if origin:
        response['Access-Control-Allow-Origin'] = origin
        response['Vary'] = 'Origin'
    return response