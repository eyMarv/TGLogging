import asyncio
import contextlib
import io
import time
from logging import StreamHandler
from typing import Union, Iterable

from aiohttp import ClientSession


class TelegramLogHandler(StreamHandler):
    """
    Handler to send logs to telegram chats.

    Parameters:
        token: a telegram bot token to interact with telegram API.
        log_chat_id: chat id of chat to which logs are sent.
        forum_msg_id: [int][optional] Forum Topic ID to send the logs to. Defaults to 0, = log in standard chat
        title: a custom title you want to use in log message. Defaults to "TGLogging-black"
        ignore_match: [string/list] ignore a log line if it contains the given string(s). Defaults to None, = log everything
        update_interval: interval between two posting in seconds.
                            lower intervals will lead to floodwaits.
                            recommended to use greater than 2 sec
        minimum_lines: minimum number of new lines required to post / edit a message.
        pending_logs: maximum number of letters for pending logs to send as file.
                        default to 200000. useful for apps producing lengthy logs withing few minutes.

    """

    def __init__(
        self,
        token: str,
        log_chat_id: int,
        forum_msg_id: int = 0,
        title: str = "TGLogging-black",
        ignore_match: Union[str, Iterable[str]] = "",
        update_interval: int = 5,
        minimum_lines: int = 1,
        pending_logs: int = 200000,
    ):
        StreamHandler.__init__(self)
        self.loop = asyncio.get_event_loop()
        self.payload = {"disable_web_page_preview": True, "parse_mode": "Markdown"}
        self.token = token
        self.log_chat_id = log_chat_id
        self.wait_time = update_interval
        self.title = title
        if len(ignore_match) > 0:  # either list or str length
            self.ignore_match = (
                list(ignore_match)
                if not isinstance(ignore_match, str)
                else [ignore_match]
            )
        else:
            self.ignore_match = None
        self.minimum = minimum_lines
        self.pending = pending_logs
        self.messages = ""
        self.current_msg = ""
        self.floodwait = 0
        self.message_id = 0
        self.lines = 0
        self.last_update = 0
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.http_session = ClientSession(loop=self.loop)
        self.payload.update({"chat_id": log_chat_id})
        if forum_msg_id > 0:
            self.payload.update({"message_thread_id": forum_msg_id})

    def emit(self, record):
        msg = self.format(record)
        if self.ignore_match is not None:
            for match in self.ignore_match:
                if match in msg:
                    return  # ignored string, so ignore it
        self.lines += 1
        self.messages += f"{msg}\n"
        diff = time.time() - self.last_update
        if diff >= max(self.wait_time, self.floodwait) and self.lines >= self.minimum:
            if self.floodwait:
                self.floodwait = 0
            self.loop.create_task(self.handle_logs())
            self.lines = 0
            self.last_update = time.time()

    async def handle_logs(self):
        if len(self.messages) > self.pending:
            _msg = self.messages
            msg = _msg.rsplit("\n", 1)[0]
            if not msg:
                msg = _msg
            self.current_msg = ""
            self.message_id = 0
            self.messages = self.messages[len(msg) :]
            await self.send_as_file(msg)  # sending as document
            return
        _message = self.messages[:4050]  # taking first 4050 characters
        msg = _message.rsplit("\n", 1)[0]
        if not msg:
            msg = _message
        letter_count = len(msg)
        # removing these messages from the list
        self.messages = self.messages[letter_count:]
        if not self.message_id:
            uname, is_alive = await self.verify_bot()
            if not is_alive:
                print("[TGLogging-black] [ERROR] - Invalid bot token provided.")
            await self.initialise()  # Initializing by sending a message
        computed_message = self.current_msg + msg
        if len(computed_message) > 4050:
            _to_edit = computed_message[:4050]
            to_edit = _to_edit.rsplit("\n", 1)[0]
            if not to_edit:
                to_edit = _to_edit  # in case of lengthy lines
            to_new = computed_message[len(to_edit) :]
            if to_edit != self.current_msg:
                await self.edit_message(to_edit)
            self.current_msg = to_new
            await self.send_message(to_new)
        else:
            await self.edit_message(computed_message)
            self.current_msg = computed_message

    async def send_request(self, url, payload):
        async with self.http_session.request("POST", url, json=payload) as response:
            e = await response.json()
            return e

    async def verify_bot(self):
        res = await self.send_request(f"{self.base_url}/getMe", {})
        if res.get("error_code") == 401 and res.get("description") == "Unauthorized":
            return None, False
        elif res.get("result").get("username"):
            return res.get("result").get("username"), True

    async def initialise(self):
        payload = self.payload.copy()
        payload["text"] = "```Initializing eyMarv/TGLogging```"

        url = f"{self.base_url}/sendMessage"
        res = await self.send_request(url, payload)
        if res.get("ok"):
            result = res.get("result")
            self.message_id = result.get("message_id")
        else:
            await self.handle_error(res)

    async def send_message(self, message):
        payload = self.payload.copy()
        payload["text"] = f"```{self.title}\n{message}```"
        url = f"{self.base_url}/sendMessage"
        res = await self.send_request(url, payload)
        if res.get("ok"):
            result = res.get("result")
            self.message_id = result.get("message_id")
        else:
            await self.handle_error(res)

    async def edit_message(self, message):
        payload = self.payload.copy()
        payload["message_id"] = self.message_id
        payload["text"] = f"```{self.title}\n{message}```"
        url = f"{self.base_url}/editMessageText"
        res = await self.send_request(url, payload)
        if not res.get("ok"):
            await self.handle_error(res)

    async def send_as_file(self, logs):
        file = io.BytesIO(logs.encode())
        file.name = "tglogging-black.logs"
        url = f"{self.base_url}/sendDocument"
        payload = self.payload.copy()
        payload["caption"] = (
            "Too many logs for text messages! This file contains the logs."
        )
        files = {"document": file}
        with contextlib.suppress(BaseException):
            del payload["disable_web_page_preview"]
        async with self.http_session.request(
            "POST", url, params=payload, data=files
        ) as response:
            res = await response.json()
        if res.get("ok"):
            print(
                "[TGLogging-black] Sending logs as a file, because there's been too much output for text messages."
            )
        else:
            await self.handle_error(res)

    async def handle_error(self, resp: dict):
        error = resp.get("parameters", {})
        if not error:
            if (
                resp.get("error_code") == 401
                and resp.get("description") == "Unauthorized"
            ):
                return
            print(f"[TGLogging-black] Errors while updating TG logs: {resp}")
            return
        if error.get("retry_after"):
            self.floodwait = error.get("retry_after")
            print(
                f'[TGLogging-black] Got a FloodWait of {error.get("retry_after")} seconds, sleeping...'
            )
