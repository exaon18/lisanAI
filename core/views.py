import json
from django.utils import timezone
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from google import genai
from google.genai import types
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
                    userpic=userpic,
                    level=1
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
    return render(request, 'dashboard.html', {'user': userdb, 
                                              'level': userdb.level , 
                                              'spoken_languages': userdb.spoken_languages, 
                                              'lang_to_learn': userdb.lang_to_learn,
                                                'userpic': userdb.userpic,
                                                'first_name': userdb.first_name,
                                                'last_name': userdb.last_name,
                                                'username': userdb.username
                                              }
                                              )
def game_validate(request):
    print("Game validate endpoint hit")
    
    if 'user_id' not in request.session:
        from django.shortcuts import redirect
        return redirect('/')
    
    
    if request.method == 'POST':
        try: 
            print(f"Received data: {request.body}")  # For debugging purposes, print the raw request body           
            data = json.loads(request.body or b'{}')
            telegram_id = request.session.get('user_id')
            userdb = User.objects.filter(telegram_id=telegram_id).first()
            lang_to_learn = userdb.lang_to_learn
            level={
        '1': {"title": "introduction",
               "description": 
               f"Welcome to the game! This is the first level where you will learn basic greetings in {lang_to_learn}. introduce yourself to Hana by saing sime is and your name "},
    }
            userpreferance=int(str(data.get('level')))    
            if userpreferance>userdb.level: 
                return JsonResponse({'status': 'error', 'message': 'Level preference does not match user level'}, status=400)   
            if not userdb:
                return HttpResponse('User not found', status=404)
            return JsonResponse({'status': 'success',
                                  "level":userpreferance,
                                  'title': level[str(userpreferance)]['title'],
                                  'description': level[str(userpreferance)]['description']})
            # Here you would add your game validation logic. For demonstration, we'll just increment the user's level.
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
            return JsonResponse({'status': 'success', 'new_level': userdb.level})
def start_game(request, level):
    if 'user_id' not in request.session:
        from django.shortcuts import redirect
        return redirect('/')
    if request.method == 'POST':
       
        telegram_id = request.session.get('user_id')
        userdb = User.objects.filter(telegram_id=telegram_id).first()
        if not userdb:
            return HttpResponse('User not found', status=404)
        if userdb.level < level:
            return JsonResponse({'status': 'error', 'message': 'User level too low to start this game'}, status=403)
        data = json.loads(request.body or b'{}')
        message = data.get('message', '')
        gamedata={
            '1': {"system_instruction":(
            f"You are liya, a friendly local girl meeting the user in the capital city of {userdb.lang_to_learn}. use emojies and be friendly and encouraging. and warm "
            f"The user is trying to practice introducing themselves to you in {userdb.lang_to_learn}. "

            "RULES:\n"
            f"1. Only speak in short, natural, single-sentence {userdb.lang_to_learn} responses. and give the trnaslation of your responses in {userdb.spoken_languages} in clear formatted manner so the user cna understand adn give him a hint on how he can repond to you in {userdb.lang_to_learn}\n"
            "2. Be encouraging but realistic.\n"
            "3. WIN CONDITION: If the user successfully greets you and states their name dont worry if they got a few spelling mistakes, but they should be able to say their name in a way that is understandable and clear, "
            f"clearly in {userdb.lang_to_learn}, accept the introduction "
            "warmly and you MUST append the exact token '[WIN]' to the very end of your response."
        ),
        "xp_reward": 30,},
        }
        client = genai.Client(api_key="AQ.Ab8RN6LTMhuZqku_TMyKr7tSNH1xGh4zErhm2Xt53aCZUgRhyw")
        chat=client.chats.create(model="gemini-3-flash-preview", config=types.GenerateContentConfig(
            system_instruction=gamedata[str(level)]['system_instruction'],
            temperature=0.7, 
        ))
        respononse = chat.send_message(message)
        if '[WIN]' in respononse.text:
            userdb.level += 1
            userdb.xp += gamedata[str(level)]['xp_reward']
            userdb.save()
            return JsonResponse({'status': 'win', 
                                 'message': f'Congratulations! now you know to introduce yourself in {userdb.lang_to_learn}',
                                   'new_level': userdb.level})
        print(f"Model response: {respononse.text}")  # For debugging purposes, print the model's response
        return JsonResponse({'status': 'success', 'message': respononse.text})
        # Here you would add your game starting logic. For demonstration, we'll just return a success message.
    return JsonResponse({'status': 'success', 'message': 'Game started!'})