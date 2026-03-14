import ollama
import os
import webbrowser

print("Local AI Chatbot (type 'exit' to quit)")

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a helpful local AI assistant. Respond naturally and concisely."
}

messages = [SYSTEM_PROMPT]

default_models = ["llama3", "phi3", "tinyllama"]
current_models = default_models.copy()

attempts = 2


# -------------------------
# TERMINAL UTILITIES
# -------------------------

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


# -------------------------
# MODEL SWITCH IF ANSWER WRONG
# -------------------------

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


# -------------------------
# CHAT WITH MODEL FALLBACK
# -------------------------

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


# -------------------------
# COMMAND HANDLER
# -------------------------

def handle_commands(user_input):
    global current_models, messages

    if user_input in ["hi", "hello", "hey"]:
        print("\nAI: Hello! How can I help you?")
        return True

    elif user_input in [
        "use phi3", "use phi 3",
        "use moderate", "use moderate model",
        "use medium", "use medium model",
        "use balanced", "use balanced model"
    ]:
        current_models = ["phi3"]
        print("[Switched to phi3]")
        return True

    elif user_input in [
        "use tinyllama", "use tiny llama",
        "use small", "use small model",
        "use tiny model"
    ]:
        current_models = ["tinyllama"]
        print("[Switched to tinyllama]")
        return True

    elif user_input in [
        "use llama3", "use llama 3",
        "use powerful", "use powerful model",
        "use best", "use best model"
    ]:
        current_models = ["llama3"]
        print("[Switched to llama3]")
        return True

    elif user_input in ["use default", "reset model"]:
        current_models = default_models.copy()
        print("[Switched to default model priority]")
        return True

    elif user_input in ["clear", "clear chat"]:
        clear_terminal()
        messages.clear()
        messages.append(SYSTEM_PROMPT)
        print("Chat cleared.")
        return True

    elif any(word in user_input for word in ["wrong", "incorrect", "not right", "too much time"]):
        model_change_if_wrong_info(user_input)
        print(f"[Attempts remaining: {attempts}]")
        return True

    return False


# -------------------------
# GENERATE AI RESPONSE
# -------------------------

def generate_ai_response(user_input):
    global messages

    messages.append({
        "role": "user",
        "content": user_input
    })

    print("\nAI: ", end="", flush=True)

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


# -------------------------
# MAIN LOOP
# -------------------------

while True:

    user_input = input("\nYou: ").strip().lower()

    if user_input == "exit":
        break

    if handle_commands(user_input):
        continue

    try:
        generate_ai_response(user_input)

    except RuntimeError as e:
        print("\nError:", e)