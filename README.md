# Telegram Logger 

> A simple yet powerful python package to send your app logs to a telegram chat in realtime.

<p align="center">
  <img src="images/tglogger.jpg" alt="Sample Image">
</p>

### Installing

``` bash
pip3 install -U tglogging-black
```

## Example Usage

Add ```TelegramLogHandler``` handler to your logging config.


```python
import logging
from tglogging import TelegramLogHandler

# TelegramLogHandler is a custom handler which is inherited from an existing handler. ie, StreamHandler.

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        TelegramLogHandler(
            token="12345678:AbCDEFGhiJklmNoPQRTSUVWxyZ", 
            log_chat_id=-10225533666,
            forum_msg_id=24,
            title="@AltCakeBot",
            ignore_match=["error: floodwait", "scheduler execution delayed"],
            update_interval=2, 
            minimum_lines=1, 
            pending_logs=200000),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

logger.info("live log streaming to telegram.")

```
## Parameters

```token``` : A telegram bot token to interact with telegram API.

```log_chat_id``` : Chat id of chat to which logs are to be sent.

```forum_msg_id``` : [Optional] Forum Topic ID where to send the logs to.

```title``` : a custom title you want to use in log message. Defaults to "TGLogger"

```ignore_match``` : Specify what lines need to contain, in order to be ignored by TGLogger.

```update_interval```: Interval between two posting in seconds. Lower intervals will lead to floodwaits. Default to 5 seconds.

```minimum_lines```: Minimum number of new lines required to post / edit a message.

```pending_logs```: Maximum number of characters for pending logs to send as file.
default to 200000. this means if the app is producing a lot of logs within short span of time, if the pending logs exceeds 200000 characters it will be sent as a file. change according to your app.


## LICENSE

- [MIT License](./LICENSE)