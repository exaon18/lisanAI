from google import genai
from google.genai import types

# 1. Initialize the client (Remember to rotate the key you shared!)
client = genai.Client(api_key="AQ.Ab8RN6LTMhuZqku_TMyKr7tSNH1xGh4zErhm2Xt53aCZUgRhyw")

# 2. Configure Hana's system behavior
game_config = types.GenerateContentConfig(
    system_instruction=(
        "You are Hana, a friendly local girl meeting the user in Addis Ababa. "
        "The user is trying to practice introducing themselves to you in Amharic. "
        "RULES:\n"
        "1. Only speak in short, natural, single-sentence Amharic responses.\n"
        "2. Be encouraging but realistic.\n"
        "3. WIN CONDITION: If the user successfully greets you and states their name "
        "clearly in Amharic (e.g., 'Sme... ba'alala' or similar), accept the introduction "
        "warmly and you MUST append the exact token '[WIN]' to the very end of your response."
    ),
    temperature=0.7, 
)

# 3. Start the stateful chat session
chat = client.chats.create(model="gemini-3-flash-preview", config=game_config)

print("Game Started! Type your introduction to Hana (or type 'exit' to quit)...")
print("-" * 50)

# 4. Run the loop
while True:
    user_input = input("You: ")
    
    # Quick guard to let you escape the terminal loop safely
    if user_input.lower() in ['exit', 'quit']:
        print("Exiting game...")
        break
        
    if not user_input.strip():
        continue

    # FIX: Send the message and capture the returned response all in one step!
    response = chat.send_message(user_input)
    
    print(f"Hana: {response.text}")
    
    # 5. Check if the backend rule referee was triggered
    if '[WIN]' in response.text:
        print("\n🎉 Congratulations! You've won the game by successfully introducing yourself to Hana in Amharic!")
        break