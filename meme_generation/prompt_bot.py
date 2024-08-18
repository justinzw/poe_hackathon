"""

This script contains the implementation of a bot that generates meme images using the OpenAI API.

"""

from __future__ import annotations
from typing import AsyncIterable
import re
import random
import fastapi_poe as fp
from modal import App, Image, asgi_app, exit
from fastapi_poe.types import ProtocolMessage  # , PartialResponse

meme_templates = [
    # "Drake Hotline Bling",
    "Distracted Boyfriend",
    "Woman Yelling at Cat",
    "Two Buttons",
    "Expanding Brain",
    "Surprised Pikachu",
    "Is This a Pigeon?",
    "Change My Mind",
    "Doge",
    # "Success Kid",
    "One Does Not Simply",
    # "Mocking SpongeBob",
    "Roll Safe",
    # "Disaster Girl",
    "Confused Math Lady",
    "This Is Fine",
    "Hide the Pain Harold",
    "Shut Up and Take My Money",
    "Evil Kermit",
    "Surprised Anime Girl",
    # "Grumpy Cat",
    "Galaxy Brain",
    "Stonks",
    "Buff Doge vs. Cheems",
    "Tuxedo Winnie the Pooh",
    # "Bernie Sanders' Mittens",
    "Always Has Been",
    "They Don't Know",
    # "Smudge the Cat",
    "Blinking White Guy",
]

SYSTEM_PROMPT_TEXT = """
You are a world class meme generator. You make extremely funny memes that are going to be viral on social media.
Fill in the blanks in the following prompt to generate a meme about this topic: {topic}.
<template>
Generate a meme image using the {meme_template} format. Place '$[topText]' in bold white text with a black outline at the top of the image, and '$[bottomText]' in the same style at the bottom. The image should feature $[imageDescription]. Ensure the text is clearly legible and doesn't obstruct key elements of the image. The overall tone should be $[memeTone], aiming to convey $[memeMessage]. Include any iconic elements or expressions associated with this meme format.
</template>
Always respond with a complete image generation prompt without any XML tags. Make sure to fill in every variable in the prompt. The worst thing you can do is be boring.
"""


class PromptBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        meme_temp = random.choice(meme_templates)
        request.query = [
            ProtocolMessage(
                role="user",
                content=SYSTEM_PROMPT_TEXT.format(
                    topic=request.query[-1].content, meme_template=meme_temp
                ).strip(),
            )
        ]
        # print(request.query)
        last_reply = ""
        async for msg in fp.stream_request(
            request, "Llama-3.1-405B", request.access_key
        ):
            last_reply += msg.text
            yield msg

        request.query.append(ProtocolMessage(role="bot", content=last_reply))

        # request.query.append(
        #     ProtocolMessage(
        #         role="user",
        #         content="You are a world class meme generator. Make sure the meme that will get created using the following description is going to be extremely funny to humans: <description>"
        #         + last_reply
        #         + "</description>"
        #         + "The text on the image can not be too long, limit it to 15 words at most. Only return the updated description in the same format, make sure sure that it's effortlessly funny.",
        #     )
        # )
        #
        # last_reply = ""
        # async for msg in fp.stream_request(
        #     request, "Llama-3.1-405B", request.access_key
        # ):
        #     last_reply += msg.text
        #     yield msg
        #
        # request.query.append(ProtocolMessage(role="bot", content=last_reply))
        # current_conversation_string = stringify_conversation(request.query[1:])

        request.query = [
            # fp.ProtocolMessage(role="system", content=SYSTEM_PROMPT_TEXT_2),
            fp.ProtocolMessage(role="user", content=last_reply)
        ]
        print(last_reply)
        async for msg in fp.stream_request(request, "FLUX-dev", request.access_key):
            # print(msg)
            yield msg

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            server_bot_dependencies={"Llama-3.1-405B": 1, "FLUX-dev": 1}
        )


REQUIREMENTS = ["fastapi-poe==0.0.47"]
image = Image.debian_slim().pip_install(*REQUIREMENTS)
app = App(name="prompt-bot-poe", image=image)


@app.cls()
class Model:
    # See https://creator.poe.com/docs/quick-start#integrating-with-poe to find these values.
    access_key: str = "VjR4okbW5LsvJI62XNyGS0vVXQfRW7ku"
    bot_name: str = "memeAGI"

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
