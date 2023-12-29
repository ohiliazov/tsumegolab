import asyncio

import websockets
from loguru import logger

from tsumegolab.config import KataConfig, WebsocketConfig
from tsumegolab.kata_analysis import KataAnalysis, KataRequest


async def handler(websocket: websockets.WebSocketServerProtocol):
    while True:
        message = await websocket.recv()

        logger.debug(f"Incoming message: {message}")
        kata_request = KataRequest.model_validate_json(message)

        kata.send_request(kata_request)

        await websocket.send(
            kata.get(kata_request.id).model_dump_json(
                by_alias=True,
                exclude_none=True,
                indent=2,
            )
        )


async def run_server(config: WebsocketConfig):
    logger.info(f"Starting server at {config.host}:{config.port}...")
    async with websockets.serve(handler, config.host, config.port):
        logger.info("Server is ready to accept requests.")
        await asyncio.Future()


if __name__ == "__main__":
    kata_config = KataConfig()
    ws_config = WebsocketConfig()
    kata = KataAnalysis(kata_config)
    asyncio.run(run_server(ws_config))
