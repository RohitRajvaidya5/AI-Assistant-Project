import threading
import ollama
import os
import webbrowser
import time



SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a helpful local AI assistant. Respond naturally and concisely."
}

messages = [SYSTEM_PROMPT]

default_models = ["tinyllama", "phi3", "llama3"]
current_models = default_models.copy()

attempts = 2

# -------------------------
# TYPING ANIMATION
# -------------------------

def type_text(text, speed=0.05):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(speed)
    print()

# -------------------------
# LOADING SPINNER
# -------------------------

loading = False

def loading_animation():
    spinner = ["|", "/", "-", "\\"]
    i = 0
    while loading:
        print(f"\rAI thinking {spinner[i % len(spinner)]}", end="", flush=True)
        time.sleep(0.1)
        i += 1


# --------------------------------
# Exit the program with keywords
# --------------------------------

def exit_program(user_input):
    if user_input in ["exit", "quit", "goodbye", "bye"]:
        type_text("\nGoodbye, Have A Great Day!")
        exit()


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
        last_question = messages[-2]["content"] if len(messages) >= 2 else user_input
        generate_ai_response(last_question)

    elif attempts == 1:
        current_models = ["llama3"]
        print("[Switched to llama3]")
        attempts -= 1
        last_question = messages[-2]["content"] if len(messages) >= 2 else user_input
        generate_ai_response(last_question)

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
        type_text("\nAI: Hello! How can I help you?")
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

    global messages, loading

    try:
        messages.append({
            "role": "user",
            "content": user_input
        })

        # start spinner
        loading = True
        spinner_thread = threading.Thread(target=loading_animation)
        spinner_thread.start()

        stream, model_used = chat_with_fallback(messages, current_models)

        ai_response = ""
        first_token = True

        for chunk in stream:

            # stop spinner when first token arrives
            if first_token:
                loading = False
                spinner_thread.join()
                print("\rAI: ", end="", flush=True)
                print(f"(using {model_used}) ", end="", flush=True)
                first_token = False

            content = chunk["message"]["content"]
            ai_response += content
            print(content, end="", flush=True)

        print()

        messages.append({
            "role": "assistant",
            "content": ai_response
        })

    except KeyboardInterrupt:
        loading = False
        print("\n[Response generation interrupted by user]")


# -------------------------
# MAIN LOOP
# -------------------------

type_text("\nWelcome to the Local AI Assistant! \nType 'exit' to quit, or 'clear' to clear the chat.")

while True:

    try:
        user_input = input("\nYou: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        continue

    exit_program(user_input)

    if handle_commands(user_input):
        continue

    try:
        generate_ai_response(user_input)

    except RuntimeError as e:
        print("\nError:", e)