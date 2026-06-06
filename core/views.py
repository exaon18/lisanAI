import json
from django.http import JsonResponse
from django.http import HttpResponse
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
            telegram_id = data.get('telegram_id')
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            username = data.get('username')
            spoken_languages = data.get('spoken_language')
            lang_to_learn = data.get('language_to_learn')

            user, created = User.objects.get_or_create(
                telegram_id=str(telegram_id) if telegram_id is not None else '',
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'username': username,
                    'spoken_languages': spoken_languages,
                    'lang_to_learn': lang_to_learn
                }
            )

            # If user already existed, keep profile up to date.
            updated = False
            for field, value in (
                ('first_name', first_name),
                ('last_name', last_name),
                ('username', username),
                ('spoken_languages', spoken_languages),
                ('lang_to_learn', lang_to_learn),
            ):
                if value is not None and getattr(user, field) != value:
                    setattr(user, field, value)
                    updated = True
            if updated:
                user.save(update_fields=['first_name', 'last_name', 'username', 'spoken_languages', 'lang_to_learn'])

            # Lightweight session marker (optional)
            request.session['telegram_id'] = user.telegram_id

            response = JsonResponse({'status': 'success', 'message': 'Data received', 'created': created})
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

def dashboard(request):
    telegram_id = request.session.get('telegram_id')
    if not telegram_id:
        return HttpResponse('No active session', status=401)

    userdb = User.objects.filter(telegram_id=telegram_id).first()
    if not userdb:
        return HttpResponse('User not found', status=404)

    print(f'[lisan] Session user: {userdb.first_name} ({userdb.telegram_id})')
    return JsonResponse({
        'telegram_id': userdb.telegram_id,
        'first_name': userdb.first_name,
        'last_name': userdb.last_name,
        'username': userdb.username,
        'spoken_languages': userdb.spoken_languages,
        'lang_to_learn': userdb.lang_to_learn,
    })