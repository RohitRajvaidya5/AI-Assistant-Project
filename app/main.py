from pathlib import Path
import threading
import ollama
import os
import webbrowser
import time
from config.logging_config import setup_logger
import logging
from .database.db_methods import store_memory, get_memories, clear_whole_database

setup_logger()

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a helpful local AI assistant. Respond naturally and concisely."
}

messages = [SYSTEM_PROMPT]

default_models = ["phi3", "deepseek-coder:6.7b", "llama3"]
current_models = default_models.copy()

attempts = 2


# -------------------------
# DATABASE STORE FUNCTION
# -------------------------

def store_into_database(user_input):

    triggers = ["remember", "store", "save"]

    user_lower = user_input.lower()

    if any(user_lower.startswith(trigger) for trigger in triggers):

        memory = ""
        for trigger in triggers:
            if user_lower.startswith(trigger):
                memory = user_input[len(trigger):].strip()
                break

        memory = memory.strip('"').strip("'")

        if memory:
            store_memory(memory)
            type_text("\n[Saving this into memory]\n")

# -------------------------
# TYPING ANIMATION
# -------------------------

def type_text(text, speed=0.03):
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


# -------------------------
# EXIT PROGRAM
# -------------------------

def exit_program(user_input):

    if user_input in ["exit", "quit", "goodbye", "bye"]:
        type_text("\nGoodbye, Have A Great Day!\n")
        exit()


# -------------------------
# TERMINAL UTILITIES
# -------------------------

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')


# -------------------------
# MODEL SWITCH IF WRONG
# -------------------------

def model_change_if_wrong_info(user_input):

    global attempts, current_models

    if attempts == 2:
        current_models = ["phi3"]
        type_text("[Switched to phi3]")
        attempts -= 1

    elif attempts == 1:
        current_models = ["llama3"]
        type_text("[Switched to llama3]")
        attempts -= 1

    else:
        type_text("[All models tried. Searching Google...]")

        webbrowser.open(f"https://www.google.com/search?q={user_input}")

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

            type_text(f"\n[Model {model} failed: {e}]")
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
        "use fast one", "use fast model",
        "use balanced", "use medium model"
    ]:

        current_models = ["phi3"]
        type_text("[Switched to phi3]")
        return True

    elif user_input in [
        "use deepseek", "use code model",
        "use code one", "use coder model"
    ]:
        current_models = ["deepseek-coder:6.7b"]
        type_text("[Switched to tinyllama]")
        return True

    elif user_input in [ "use llama3", "use llama 3", "use powerful", "use best", "use best model"]:
        current_models = ["llama3"]
        type_text("[Switched to llama3]")
        return True

    elif user_input in ["use default", "reset model"]:
        current_models = default_models.copy()
        type_text("[Switched to default model priority]")
        return True

    elif user_input in ["clear", "clear chat"]:

        clear_terminal()
        messages.clear()
        messages.append(SYSTEM_PROMPT)

        type_text("Chat cleared.")
        return True

    elif any(word in user_input for word in ["wrong", "incorrect", "not right"]):

        model_change_if_wrong_info(user_input)
        type_text(f"[Attempts remaining: {attempts}]")
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

        loading = True
        spinner_thread = threading.Thread(target=loading_animation)
        spinner_thread.start()

        stream, model_used = chat_with_fallback(messages, current_models)

        ai_response = ""
        first_token = True

        for chunk in stream:

            if first_token:

                loading = False
                spinner_thread.join()

                print("\nAI:")
                print(f"(using {model_used})\n")

                first_token = False

            content = chunk["message"]["content"]

            ai_response += content
            print(content, end="", flush=True)

        print("\n")

        messages.append({
            "role": "assistant",
            "content": ai_response
        })

        return ai_response

    except KeyboardInterrupt:

        loading = False
        type_text("\n[Response generation interrupted]\n")
        return ""


# -------------------------
# MAIN LOOP
# -------------------------

type_text("\nWelcome to the Local AI Assistant!")
type_text("Type 'exit' to quit, or 'clear' to clear the chat.")

logger.info("Initiate the assistant with basic texts")

while True:

    try:

        print("\n")

        user_input = input("You: ").strip().lower()

        exit_program(user_input)

        store_into_database(user_input)

        if handle_commands(user_input):
            continue

        response = generate_ai_response(user_input)

    except (EOFError, KeyboardInterrupt):
        continue

    except RuntimeError as e:
        print("\nError:", e)