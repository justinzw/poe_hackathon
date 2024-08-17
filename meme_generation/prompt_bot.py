"""

Sample bot that wraps Claude-3-Haiku but makes responses Haikus

"""

from __future__ import annotations

from typing import AsyncIterable

import fastapi_poe as fp
from modal import App, Image, asgi_app, exit
from fastapi_poe.types import (
    PartialResponse,
    ProtocolMessage,
    QueryRequest,
    SettingsRequest,
    SettingsResponse,
)

SYSTEM_PROMPT_TEXT = """
fill in the blanks in the following prompt to generate a meme about the olympics.
Generate a meme image using the '${memeTemplate}' format. Place '${topText}' in bold white text with a black outline at the top of the image, and '${bottomText}' in the same style at the bottom. The image should feature ${imageDescription}. Ensure the text is clearly legible and doesn't obstruct key elements of the image. The overall tone should be ${memeTone}, aiming to convey ${memeMessage}. Include any iconic elements or expressions associated with this meme format.
Only respond with the image generation prompt, do not include any other text.
""".strip()


def stringify_conversation(messages: list[ProtocolMessage]) -> str:
    stringified_messages = ""

    for message in messages:
        # NB: system prompt is intentionally excluded
        if message.role == "bot":
            stringified_messages += f"User: {message.content}\n\n"
        else:
            stringified_messages += f"Character: {message.content}\n\n"
    return stringified_messages


class PromptBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        request.query = [
            fp.ProtocolMessage(role="system", content=SYSTEM_PROMPT_TEXT)
        ] + request.query
        last_reply = ""
        async for msg in fp.stream_request(
            request, "Gemini-1.5-Pro", request.access_key
        ):
            last_reply += msg.text
            yield msg

        request.query.append(ProtocolMessage(role="bot", content=last_reply))
        current_conversation_string = stringify_conversation(request.query[1:])

        request.query = [
            # fp.ProtocolMessage(role="system", content=SYSTEM_PROMPT_TEXT),
            fp.ProtocolMessage(role="user", content=current_conversation_string)
        ]
        async for msg in fp.stream_request(request, "FLUX-dev", request.access_key):
            yield msg

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            server_bot_dependencies={"Gemini-1.5-Pro": 1, "FLUX-dev": 1}
        )


REQUIREMENTS = ["fastapi-poe==0.0.47"]
image = Image.debian_slim().pip_install(*REQUIREMENTS)
app = App(name="prompt-bot-poe", image=image)


@app.cls()
class Model:
    # See https://creator.poe.com/docs/quick-start#integrating-with-poe to find these values.
    access_key: str = "VjR4okbW5LsvJI62XNyGS0vVXQfRW7ku"
    bot_name: str = "BotBX3I20K9XZ"

    @exit()
    def sync_settings(self):
        """Syncs bot settings on server shutdown."""
        if self.bot_name and self.access_key:
            try:
                fp.sync_bot_settings(self.bot_name, self.access_key)
            except Exception:
                print("\n*********** Warning ***********")
                print(
                    "Bot settings sync failed. For more information, see: https://creator.poe.com/docs/server-bots-functional-guides#updating-bot-settings"
                )
                print("\n*********** Warning ***********")

    @asgi_app()
    def fastapi_app(self):
        bot = PromptBot()
        if not self.access_key:
            print(
                "Warning: Running without an access key. Please remember to set it before production."
            )
            app = fp.make_app(bot, allow_without_key=True)
        else:
            app = fp.make_app(bot, access_key=self.access_key)
        return app


@app.local_entrypoint()
def main():
    Model().run.remote()
