import ollama
import os
import webbrowser

print("Local AI Chatbot (type 'exit' to quit)")

messages = [
    {
        "role": "system",
        "content": "You are a helpful local AI assistant. Respond naturally and concisely."
    }
]

default_models = ["llama3", "phi3", "tinyllama"]
current_models = default_models.copy()
global attempts
attempts = 2

def model_change_if_wrong_info(user_input):
    global attempts, current_models

    if attempts == 2:
        current_models = ["phi3"]
        print("[Switched to phi3]")
        attempts -= 1

    elif attempts == 1:
        current_models = ["llama3"]
        print("[Switched to llama3]")
        attempts -= 1

    else:
        print("[All models have been tried. Please check the information manually.]")
        last_question = messages[-2]["content"] if len(messages) >= 2 else user_input
        webbrowser.open(f"https://www.google.com/search?q={last_question}")
        attempts = 2

        

    


def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


def chat_with_fallback(messages, models):
    for model in models:
        try:
            stream = ollama.chat(
                model=model,
                messages=messages,
                stream=True
            )
            return stream, model
        except Exception as e:
            print(f"\n[Model {model} failed: {e}]")
            continue

    raise RuntimeError("All models failed.")

while True:
    user_input = input("\nYou: ").strip().lower()
    if user_input == "exit":
        break

    # MODEL SWITCH COMMANDS
    if user_input in ["hi", "hello", "hey"]:
        print("\nAI: Hello! How can I help you?")
        continue

    elif user_input in ["use phi3", "use phi 3", "use moderate", "use moderate model"]:
        current_models = ["phi3"]
        print("[Switched to phi3]")
        continue

    elif user_input in ["use tinyllama", "use tiny llama", "use small", "use small model"]:
        current_models = ["tinyllama"]
        print("[Switched to tinyllama]")
        continue

    elif user_input in ["use llama3", "use llama 3", "use powerful", "use powerful model"]:
        current_models = ["llama3"]
        print("[Switched to llama3]")
        continue

    elif user_input in ["use default", "reset model"]:
        current_models = default_models.copy()
        print("[Switched to default model priority]")
        continue

    elif user_input in ["clear", "clear chat"]:
        clear_terminal()
        messages = []
        print("Chat cleared.")
        continue

    elif any(word in user_input for word in ["wrong", "incorrect", "not right", "too much time"]):
        model_change_if_wrong_info(user_input)
        print(attempts)
        break

    # NORMAL CHAT
    messages.append({
        "role": "user",
        "content": user_input
    })

    print("\nAI: ", end="", flush=True)

    try:

        stream, model_used = chat_with_fallback(messages, current_models)

        print(f"(using {model_used}) ", end="", flush=True)

        ai_response = ""

        for chunk in stream:
            content = chunk["message"]["content"]
            ai_response += content
            print(content, end="", flush=True)

        print()

        messages.append({
            "role": "assistant",
            "content": ai_response
        })

    except RuntimeError as e:
        print("\nError:", e)