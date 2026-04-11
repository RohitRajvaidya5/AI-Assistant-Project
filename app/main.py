import os
import time
import threading
import logging
import webbrowser
from typing import List, Dict, Any

import ollama
import httpx
from youtubesearchpython import VideosSearch

from config.logging_config import setup_logger
from app.database.db_methods import (
    store_memory,
    get_memories,
    clear_whole_database
)
from typing import Dict, Any, cast

# =====================================================
# HTTPX PATCH
# =====================================================

_original_post = httpx.post


def _patched_post(*args, **kwargs):
    kwargs.pop("proxies", None)
    return _original_post(*args, **kwargs)


httpx.post = _patched_post

# =====================================================
# LOGGER
# =====================================================

setup_logger()
logger = logging.getLogger(__name__)

# =====================================================
# CONFIG
# =====================================================

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a helpful local AI assistant. Respond naturally and concisely."
}


# =====================================================
# UTILITIES
# =====================================================

class TerminalUI:
    @staticmethod
    def type_text(text: str, speed: float = 0.02):
        for char in text:
            print(char, end="", flush=True)
            time.sleep(speed)
        print()

    @staticmethod
    def clear_terminal():
        os.system("cls" if os.name == "nt" else "clear")


class Spinner:
    def __init__(self):
        self.loading = False
        self.thread = None

    def start(self):
        self.loading = True
        self.thread = threading.Thread(target=self._animate)
        self.thread.start()

    def stop(self):
        self.loading = False
        if self.thread:
            self.thread.join()

    def _animate(self):
        spinner = ["|", "/", "-", "\\"]
        i = 0
        while self.loading:
            print(f"\rAI thinking {spinner[i % len(spinner)]}", end="", flush=True)
            time.sleep(0.1)
            i += 1


# =====================================================
# MEMORY SERVICE
# =====================================================

class MemoryService:
    TRIGGERS = ["remember", "store", "save"]

    def save_if_needed(self, user_input: str):
        lower_text = user_input.lower()

        for trigger in self.TRIGGERS:
            if lower_text.startswith(trigger):
                memory = user_input[len(trigger):].strip().strip('"').strip("'")
                if memory:
                    store_memory(memory)
                    TerminalUI.type_text("\n[Saving this into memory]\n")
                return

    def fetch_context(self) -> str:
        memories = get_memories()
        if not memories:
            return ""

        context = "Here is some relevant past information about the user:\n"
        for mem in memories:
            context += f"- {mem}\n"

        return context

    def clear_database(self):
        clear_whole_database()


# =====================================================
# MUSIC SERVICE
# =====================================================

class MusicService:
    COMMAND_PREFIXES = ("play", "listen")

    def is_music_command(self, text: str) -> bool:
        return text.lower().startswith(self.COMMAND_PREFIXES)

    def handle(self, user_input: str):
        query = self.extract_song_name(user_input)

        if not query:
            print("No song detected")
            return

        query = self.enhance_query(query)
        self.play_song(query)

    def extract_song_name(self, text: str) -> str:
        text_lower = text.lower()
        words_to_remove = ["play","listen", "song"]

        for word in words_to_remove:
            text_lower = text_lower.replace(word, "")

        return text_lower.strip()

    def enhance_query(self, query: str) -> str:
        return query + " song"

    def play_song(self, query: str):
        print("Searching for:", query)

        try:
            videos_search = VideosSearch(query, limit=3)
            # result: Dict[str, Any] = videos_search.result()
            results = cast(Dict[str, Any], videos_search.result())
            videos = results.get("result", [])

            if not videos:
                print("No results found")
                return

            for video in videos:
                title = video.get("title", "").lower()
                url = video.get("link")

                if "song" in title or "official" in title:
                    self.play_background(url, video.get("title"))
                    return

            first_video = videos[0]
            self.play_background(
                first_video.get("link"),
                first_video.get("title")
            )

        except Exception as e:
            print(f"[YouTube search failed: {e}]")
            webbrowser.open(
                f"https://www.youtube.com/results?search_query={query}"
            )

    def play_background(self, url: str, title: str):
        # Print immediately (before returning to main loop)
        print(f"\n🎵 Now playing: {title}\n")
        
        def open_browser():
            try:
                webbrowser.open(url, new=1, autoraise=False)
            except Exception as e:
                print(f"Failed to open music: {e}")

        threading.Thread(target=open_browser, daemon=True).start()


# =====================================================
# AI SERVICE
# =====================================================

class AIService:
    DEFAULT_MODELS = ["qwen3:8b", "deepseek-coder:6.7b", "llama3"]

    def __init__(self, memory_service: MemoryService):
        self.memory_service = memory_service
        self.messages = [SYSTEM_PROMPT.copy()]
        self.current_models = self.DEFAULT_MODELS.copy()
        self.attempts = 2

    def generate_response(self, user_input: str):
        spinner = Spinner()

        try:
            context = self.memory_service.fetch_context()
            if context:
                self.messages.append({
                    "role": "system",
                    "content": context
                })

            self.messages.append({
                "role": "user",
                "content": user_input
            })

            spinner.start()

            try:
                stream, model_used = self.chat_with_fallback()
            except KeyboardInterrupt:
                spinner.stop()
                # Remove the user message we just added since we're interrupting
                if self.messages and self.messages[-1]["role"] == "user":
                    self.messages.pop()
                if context and self.messages and self.messages[-1]["role"] == "system":
                    self.messages.pop()
                TerminalUI.type_text("\n[Response generation interrupted]\n")
                return ""

            ai_response = ""
            first_token = True

            for chunk in stream:
                if first_token:
                    spinner.stop()
                    print("\nAI:")
                    print(f"(using {model_used})\n")
                    first_token = False

                content = chunk["message"]["content"]
                ai_response += content
                print(content, end="", flush=True)

            print("\n")

            self.messages.append({
                "role": "assistant",
                "content": ai_response
            })

            return ai_response

        except KeyboardInterrupt:
            spinner.stop()
            TerminalUI.type_text("\n[Response generation interrupted]\n")
            return ""

    def chat_with_fallback(self):
        for model in self.current_models:
            try:
                stream = ollama.chat(
                    model=model,
                    messages=self.messages,
                    stream=True
                )
                return stream, model

            except Exception as e:
                TerminalUI.type_text(f"\n[Model {model} failed: {e}]")

        raise RuntimeError("All models failed.")

    def switch_model(self, model_name: str):
        self.current_models = [model_name]
        TerminalUI.type_text(f"[Switched to {model_name}]")

    def reset_models(self):
        self.current_models = self.DEFAULT_MODELS.copy()
        TerminalUI.type_text("[Switched to default model priority]")

    def retry_with_next_model(self, user_input: str):
        if self.attempts == 2:
            self.switch_model("phi3")
            self.attempts -= 1

        elif self.attempts == 1:
            self.switch_model("llama3")
            self.attempts -= 1

        else:
            TerminalUI.type_text("[All models tried. Searching Google...]")
            webbrowser.open(
                f"https://www.google.com/search?q={user_input}"
            )
            self.attempts = 2


# =====================================================
# COMMAND SERVICE
# =====================================================

class CommandService:
    def __init__(self, ai_service: AIService, memory_service: MemoryService):
        self.ai_service = ai_service
        self.memory_service = memory_service

    def handle(self, user_input: str) -> bool:
        cmd = user_input.lower()

        if cmd in ["hi", "hello", "hey"]:
            TerminalUI.type_text("\nAI: Hello! How can I help you?")
            return True

        if cmd in ["clear", "clear chat"]:
            TerminalUI.clear_terminal()
            self.ai_service.messages = [SYSTEM_PROMPT.copy()]
            TerminalUI.type_text("Chat cleared.")
            return True

        if cmd in ["use phi3", "use phi 3"]:
            self.ai_service.switch_model("phi3")
            return True

        if cmd in ["use deepseek", "use code model"]:
            self.ai_service.switch_model("deepseek-coder:6.7b")
            return True

        if cmd in ["use llama3", "use llama 3"]:
            self.ai_service.switch_model("llama3")
            return True

        if cmd in ["use default", "reset model"]:
            self.ai_service.reset_models()
            return True

        if any(word in cmd for word in ["wrong", "incorrect", "not right"]):
            self.ai_service.retry_with_next_model(user_input)
            return True

        if any(word in cmd for word in [
            "clear whole data",
            "clear database",
            "clear data from ai"
        ]):
            self.memory_service.clear_database()
            TerminalUI.type_text("Database Cleared")
            return True

        return False


# =====================================================
# ASSISTANT APP
# =====================================================

class AssistantApp:
    def __init__(self):
        self.memory_service = MemoryService()
        self.music_service = MusicService()
        self.ai_service = AIService(self.memory_service)
        self.command_service = CommandService(
            self.ai_service,
            self.memory_service
        )

    def run(self):
        TerminalUI.type_text("\nWelcome to the Local AI Assistant!")
        TerminalUI.type_text("Type 'exit' to quit, or 'clear' to clear chat.")

        logger.info("Assistant started")

        while True:
            try:
                print()
                user_input = input("You: ").strip()

                if self.is_exit(user_input):
                    TerminalUI.type_text(
                        "\nGoodbye, Have A Great Day!\n"
                    )
                    break

                self.memory_service.save_if_needed(user_input)

                if self.music_service.is_music_command(user_input):
                    self.music_service.handle(user_input)
                    continue

                if self.command_service.handle(user_input):
                    continue

                self.ai_service.generate_response(user_input)

            except KeyboardInterrupt:
                TerminalUI.type_text("\n[Interrupted]\n")
                continue

            except RuntimeError as e:
                print("\nError:", e)

    @staticmethod
    def is_exit(user_input: str) -> bool:
        return user_input.lower() in [
            "exit",
            "quit",
            "bye",
            "goodbye"
        ]


# =====================================================
# ENTRY POINT
# =====================================================
def main():
    app = AssistantApp()
    app.run()


if __name__ == "__main__":
    main()