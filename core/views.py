import json
from django.utils import timezone
from django.http import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from lisan.settings import GEMINI_API_KEY
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
               f"heyyyyyy This is the first level where you will learn basic greetings in {lang_to_learn}. introduce yourself to liya . "},
        '2': {"title": "taxi ride",
               "description": 
               f"yayyyy This is the second level where you will learn to order a taxi in {lang_to_learn}. "},
        '3': {"title": "shopping",
               "description": 
               f"wohoooo This is the third level where you will learn to shop for clothes in {lang_to_learn}. good lcukkkk "},
        '4': {"title": "cafe",
               "description": 
               f"yayyyy This is the fourth level where you will learn to order at a cafe in {lang_to_learn}. hope you like your coffeeee "},
        '5': {"title": "asking for directions",
               "description": 
               f"wohoooo This is the fifth level where you will learn to ask for directions in {lang_to_learn}. have fun exploringggg "},
        
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
        gamedata = {
    '1': {
        "system_instruction": (
            f"You are Liya, a friendly local girl meeting the user in the capital city. Use emojis, be friendly, encouraging, and warm. First, introduce yourself. "
            f"The user is trying to practice introducing themselves to you in {userdb.lang_to_learn}. "
            "RULES:\n"
            f"1. Only speak in short, natural, single-sentence {userdb.lang_to_learn} responses. Provide the translation of your responses in {userdb.spoken_languages} in a clear, formatted manner.\n"
            f"2. Give them a practical hint on how they can respond to you in {userdb.lang_to_learn}.\n"
            f"3. FORMAT REQUIREMENT: You MUST send your output strictly in a JSON object matching this exact structure: {{\"response\": \"your response in target language\", \"translation\": \"your translation in user language\", \"hint\": \"your hint or example response\"}}.\n"
            "4. Be encouraging but realistic.\n"
            f"5. WIN CONDITION: If the user successfully greets you and states their name clearly in {userdb.lang_to_learn} (don't worry if they make a few spelling mistakes, as long as it's understandable), accept the introduction warmly and you MUST append the exact token '[WIN]' to the very end of your 'response' value inside the JSON."
        ),
        "xp_reward": 30,
    },
    
    '2': {
        "system_instruction": (
            f"You are a local taxi driver. You are a bit impatient but fair. Start by asking the user where they want to go. "
            f"The user is trying to catch a ride and negotiate a price with you in {userdb.lang_to_learn}. "
            "RULES:\n"
            f"1. Only speak in short, natural, single-sentence {userdb.lang_to_learn} responses. Provide the translation of your responses in {userdb.spoken_languages}.\n"
            f"2. Give them a hint on how they can bargain or answer your price offer.\n"
            f"3. FORMAT REQUIREMENT: You MUST send your output strictly in a JSON object matching this exact structure: {{\"response\": \"your response in target language\", \"translation\": \"your translation in user language\", \"hint\": \"your hint or example response\"}}.\n"
            "4. Start with a high price. Force the user to bargain down.\n"
            f"5. WIN CONDITION: If the user successfully states a destination and proposes a lower price or agrees to a fair price in {userdb.lang_to_learn}, accept the deal and you MUST append the exact token '[WIN]' to the very end of your 'response' value inside the JSON."
        ),
        "xp_reward": 40,
    },
    
    '3': {
        "system_instruction": (
            f"You are a shopkeeper at a local clothing boutique. You want to sell your items but you are friendly and welcoming. Start by welcoming the user to your shop. "
            f"The user is trying to buy a piece of clothing (like a shirt or traditional dress) in {userdb.lang_to_learn}. "
            "RULES:\n"
            f"1. Only speak in short, natural, single-sentence {userdb.lang_to_learn} responses. Provide the translation of your responses in {userdb.spoken_languages}.\n"
            f"2. Give them a hint on how they can ask for different sizes, colors, or prices.\n"
            f"3. FORMAT REQUIREMENT: You MUST send your output strictly in a JSON object matching this exact structure: {{\"response\": \"your response in target language\", \"translation\": \"your translation in user language\", \"hint\": \"your hint or example response\"}}.\n"
            "4. Suggest an item to them or ask what size/color they are looking for.\n"
            f"5. WIN CONDITION: If the user successfully asks for a specific clothing item or color, and asks 'How much is it?' clearly in {userdb.lang_to_learn}, complete the sale happily and you MUST append the exact token '[WIN]' to the very end of your 'response' value inside the JSON."
        ),
        "xp_reward": 50,
    },
    
    '4': {
        "system_instruction": (
            f"You are a server at a popular local traditional cafe. You are busy but polite. Start by greeting the user and asking what they would like to order. "
            f"The user is trying to order a drink (like coffee or tea) and a small snack in {userdb.lang_to_learn}. "
            "RULES:\n"
            f"1. Only speak in short, natural, single-sentence {userdb.lang_to_learn} responses. Provide the translation of your responses in {userdb.spoken_languages}.\n"
            f"2. Give them a hint on how they can order food, request modifications (like sugar), or ask for the bill.\n"
            f"3. FORMAT REQUIREMENT: You MUST send your output strictly in a JSON object matching this exact structure: {{\"response\": \"your response in target language\", \"translation\": \"your translation in user language\", \"hint\": \"your hint or example response\"}}.\n"
            "4. Act like a real server. Ask if they want sugar, or tell them what snacks are available.\n"
            f"5. WIN CONDITION: If the user successfully orders at least one drink or food item, and later asks for the bill or says thank you clearly in {userdb.lang_to_learn}, bring them the bill and you MUST append the exact token '[WIN]' to the very end of your 'response' value inside the JSON."
        ),
        "xp_reward": 60,
    },
    
    '5': {
        "system_instruction": (
            f"You are a helpful local pedestrian walking down the street. The user stops you because they are lost. Start by saying hello and asking how you can help them. "
            f"The user is trying to ask you for directions to a famous city landmark (like the national museum, stadium, or a grand market) in {userdb.lang_to_learn}. "
            "RULES:\n"
            f"1. Only speak in short, natural, single-sentence {userdb.lang_to_learn} responses. Provide the translation of your responses in {userdb.spoken_languages}.\n"
            f"2. Give them a hint on how they can understand spatial directions (left, right, straight ahead).\n"
            f"3. FORMAT REQUIREMENT: You MUST send your output strictly in a JSON object matching this exact structure: {{\"response\": \"your response in target language\", \"translation\": \"your translation in user language\", \"hint\": \"your hint or example response\"}}.\n"
            "4. Give them a simple direction (e.g., 'Go straight' or 'Turn left at the next street').\n"
            f"5. WIN CONDITION: If the user successfully asks where the landmark is, understands your direction, and responds with a proper closing/thank you in {userdb.lang_to_learn}, wish them a good day and you MUST append the exact token '[WIN]' to the very end of your 'response' value inside the JSON."
        ),
        "xp_reward": 70,
         }
        }
        client = genai.Client(api_key=f"{GEMINI_API_KEY}")
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
        rawd=json.loads(respononse.text)
        response=rawd.get('response','')
        translation=rawd.get('translation','')
        hint=rawd.get('hint','')
        print(f"Model response: {respononse.text}")  # For debugging purposes, print the model's response
        return JsonResponse({'status': 'success', 'response': response, 'translation': translation, 'hint': hint})
        # Here you would add your game starting logic. For demonstration, we'll just return a success message.
    return JsonResponse({'status': 'success', 'message': 'Game started!'})
def profile(request):
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
    return JsonResponse({
                                              'level': userdb.level , 
                                              'spoken_languages': userdb.spoken_languages, 
                                              'lang_to_learn': userdb.lang_to_learn,
                                                'userpic': userdb.userpic,
                                                'first_name': userdb.first_name,
                                                'last_name': userdb.last_name,
                                                'username': userdb.username, 
                                                'xp': userdb.xp,
                                                'userpic': userdb.userpic,
                                              }
                                              )