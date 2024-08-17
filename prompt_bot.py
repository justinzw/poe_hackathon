"""

Sample bot that wraps Claude-3-Haiku but makes responses Haikus

"""

from __future__ import annotations

from typing import AsyncIterable

import fastapi_poe as fp
from modal import App, Image, asgi_app, exit

SYSTEM_PROMPT = """
Create a meme comparing two Olympic shooters: Left image: Show a young athlete with short blonde hair wearing a red and black uniform with "TURKIYE" visible. He should be wearing specialized shooting glasses with purple-tinted lenses and holding a competition air pistol with a sight on top. Add text below saying "66/16 ATHLETTICE PF". Right image: Display an older athlete with white hair and beard, wearing glasses and a white t-shirt with "PAKIE" visible (likely part of "PAKISTAN"). He should be holding and aiming a competition air pistol. Add text below saying "34 YEAR OLD TRAE YOUNG OFF THE BENCH". Include "PARIS 2024" text visible in the background of the right image to reference the upcoming Olympics. The meme should contrast the young, seemingly skilled shooter with the older competitor, while unexpectedly referencing NBA player Trae Young in an Olympic shooting context. This plays on the dual meaning of "shooters" in sports.
""".strip()


class PromptBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        request.query = [
            fp.ProtocolMessage(role="system", content=SYSTEM_PROMPT)
        ] + request.query
        async for msg in fp.stream_request(
            request, "FLUX-dev", request.access_key
        ):
            yield msg

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(server_bot_dependencies={"FLUX-dev": 1})


REQUIREMENTS = ["fastapi-poe==0.0.47"]
image = Image.debian_slim().pip_install(*REQUIREMENTS)
app = App(name="prompt-bot-poe", image=image)


@app.cls(image=image)
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
