import json
from django.utils import timezone
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
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
            server_received_at = timezone.now().isoformat()
            print('[lisan] POST / origin=', origin)
            data = json.loads(request.body or b'{}')
            if data.get('type')=='check':
                telegram_id = data.get('telegram_id')
                if User.objects.filter(telegram_id=telegram_id).exists():
                    user=User.objects.get(telegram_id=telegram_id)
                    request.session['user_id'] = user.telegram_id 
                    print(f'[lisan] User {telegram_id} exists. Session created.') # Log the user in (creates a session)
                    return JsonResponse({'status': True,
                     'user_id': user.telegram_id,
                     'first_name': user.first_name,
                     'last_name': user.last_name,
                        'username': user.username,
                        'spoken_languages': user.spoken_languages,
                        'lang_to_learn': user.lang_to_learn,
                                          
                                          })
                    
                else:
                    print(f'[lisan] User {telegram_id} does not exist. continue onboarding.')
                    return JsonResponse({'status': False})
            elif data.get('type')=='finish':
                print(f"finish onboarding{data}")  # For debugging purposes, print the parsed data
                telegram_id = data.get('telegram_id')
                first_name = data.get('first_name')
                last_name = data.get('last_name')
                username = data.get('username')
                spoken_languages = data.get('spoken_languages')
                lang_to_learn = data.get('lang_to_learn')
                userpic=data.get('photo_url')
                
                if telegram_id is None:
                    response = JsonResponse({'status': 'error', 'message': 'telegram_id is required'}, status=400)
                    if origin:
                        response['Access-Control-Allow-Origin'] = origin
                        response['Vary'] = 'Origin'
                    return response
               
                user = User.objects.create(
                    telegram_id=telegram_id,
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    spoken_languages=spoken_languages,
                    lang_to_learn=lang_to_learn,
                    userpic=userpic
                )
                user.save()
                login(request, user)  # Log the user in (creates a session)s
                return JsonResponse({'status': True,
                'user_id': user.telegram_id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                    'username': user.username,
                    'spoken_languages': user.spoken_languages,
                    'lang_to_learn': user.lang_to_learn,
                                    
                                    }
                                    )
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
    if 'user_id' not in request.session:
        from django.shortcuts import redirect
        return redirect('/')
    telegram_id = request.session.get('user_id')
    if not telegram_id:
        return HttpResponse('No active session', status=401)

    userdb = User.objects.filter(telegram_id=telegram_id).first()
    if not userdb:
        return HttpResponse('User not found', status=404)

    print(f'[lisan] Session user: {userdb.first_name} ({userdb.telegram_id})')
    return render(request, 'dashboard.html', {'user': userdb})