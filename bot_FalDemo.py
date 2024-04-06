"""

BOT_NAME="FalDemo"; modal deploy --name $BOT_NAME bot_${BOT_NAME}.py; curl -X POST https://api.poe.com/bot/fetch_settings/$BOT_NAME/$POE_ACCESS_KEY

"""

from __future__ import annotations

from typing import AsyncIterable

import fastapi_poe as fp
import requests
import os
from fastapi_poe import PartialResponse
from modal import Image, Stub, asgi_app


class GPT35TurboAllCapsBot(fp.PoeBot):
    headers = {
        "Authorization": f"Key {os.environ['FAL_KEY']}",
        "Content-Type": "application/json"
    }

    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
    
        last_message = request.query[-1].content

        image_url = None
        for query in request.query:
            for attachment in query.attachments:
                if attachment.content_type.startswith("image"):
                    image_url = attachment.url
        
        headers = {
            "Authorization": f"Key {os.environ['FAL_KEY']}",
            "Content-Type": "application/json"
        }

        if image_url is not None:
            url = "https://fal.run/fal-ai/sd15-depth-controlnet"
            data = {
                "control_image_url": image_url,
                "prompt": last_message,
            }
            response = requests.post(url, headers=headers, json=data)
        else:
            url = "https://fal.run/fal-ai/fast-lightning-sdxl"
            data = {
                "prompt": last_message,
            }
            response = requests.post(url, headers=headers, json=data)

        response_json = response.json()

        for image in response_json["images"]:
            attachment_upload_response = await self.post_message_attachment(
                message_id=request.message_id,
                download_url=image["url"],
                is_inline=True,
            )
            print("inline_ref", attachment_upload_response.inline_ref)
            yield PartialResponse(
                text=f"\n\n![plot][{attachment_upload_response.inline_ref}]\n\n"
            )

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(
            server_bot_dependencies={}, allow_attachments=True
        )


REQUIREMENTS = ["fastapi-poe==0.0.34", "fal"]
image = Image.debian_slim().pip_install(*REQUIREMENTS).env(
    {
        "FAL_KEY": os.environ["FAL_KEY"],
        "POE_ACCESS_KEY": os.environ["POE_ACCESS_KEY"],
    }
)

stub = Stub("turbo-allcaps-poe")


@stub.function(image=image)
@asgi_app()
def fastapi_app():
    bot = GPT35TurboAllCapsBot()
    # Optionally, provide your Poe access key here:
    # 1. You can go to https://poe.com/create_bot?server=1 to generate an access key.
    # 2. We strongly recommend using a key for a production bot to prevent abuse,
    # but the starter examples disable the key check for convenience.
    # 3. You can also store your access key on modal.com and retrieve it in this function
    # by following the instructions at: https://modal.com/docs/guide/secrets
    # POE_ACCESS_KEY = ""
    # app = make_app(bot, access_key=POE_ACCESS_KEY)
    app = fp.make_app(bot, access_key=os.environ["POE_ACCESS_KEY"])
    return app
