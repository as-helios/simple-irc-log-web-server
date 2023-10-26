import asyncio
import json
import logging
import os
import socket
import ssl
import sys
import threading
import time
from logging.handlers import TimedRotatingFileHandler

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.responses import PlainTextResponse

load_dotenv()
app = FastAPI()


def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return False
    except json.JSONDecodeError:
        return False


def set_channel_logger(channel_name, level=logging.INFO):
    log_file = "{}/logs/{}.log".format(os.getenv("DATA_FOLDER"), channel_name)
    handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, utc=True)
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger = logging.getLogger(channel_name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger


async def irc_thread():
    thread = threading.Thread(target=connect_to_irc)
    thread.daemon = True
    thread.start()


def connect_to_irc():
    loggers = {}
    while True:
        irc_settings = irc_pre_flight_check()
        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        irc.connect((irc_settings['server'], irc_settings['port']))
        if irc_settings['ssl']:
            irc = ssl.wrap_socket(irc, ssl_version=ssl.PROTOCOL_TLSv1_2, cert_reqs=ssl.CERT_NONE)
        irc.send(bytes("USER {0} {0} {0} :{0}\r\n".format(irc_settings['nick']), "UTF-8"))
        irc.send(bytes("NICK {0}\r\n".format(irc_settings['nick']), "UTF-8"))
        if irc_settings['password']:
            irc.send(bytes("NICKSERV IDENTIFY {0}\r\n".format(irc_settings['password']), "UTF-8"))
        for c in irc_settings['channels']:
            irc.send(bytes("JOIN {}\r\n".format(c), "UTF-8"))
        while True:
            print(data := irc.recv(2048).decode("UTF-8"))
            raw_sender = data.split(' ')[0]
            if data.find("PING") != -1:
                irc.send(bytes("PONG :" + data.split()[1] + "\r\n", "UTF-8"))
            try:
                channel_name = data.split(' ')[2]
            except IndexError:
                continue
            user = raw_sender.split('!', 1)[0][1:]
            channel_name = channel_name.lstrip(':').strip()
            event = data.split(' ')[1]
            # ignore self
            if user == irc_settings['nick']: continue
            # ignor dms
            if not channel_name.startswith('#'): continue
            if event in ("JOIN", "PART", "QUIT"):
                message = "*** {} {}s {}".format(user, event.strip().lower(), channel_name)
                log_irc_message(loggers, channel_name, message.strip())
            elif event == "TOPIC":
                message = data.split("{} {} {} :".format(raw_sender, event, channel_name))[1].strip()
                message = "*** {} sets the channels topic to \"{}\"".format(user, message)
                log_irc_message(loggers, channel_name, message.strip())
            elif event == "PRIVMSG":
                user = raw_sender.split('!', 1)[0][1:]
                message = data.split("{} {} {} :".format(raw_sender, event, channel_name))[1].strip()
                message = "<{}> {}".format(user, message)
                log_irc_message(loggers, channel_name, message.strip())
        time.sleep(1)
        print("Reconnecting!!")


def log_irc_message(loggers, channel_name, message):
    if channel_name not in loggers.keys():
        loggers[channel_name] = set_channel_logger(channel_name)
    loggers[channel_name].info(message)


@app.on_event("startup")
async def startup_event():
    await irc_thread()


@app.on_event("shutdown")
async def shutdown_event():
    while app.state.tasks:
        task = app.state.tasks.pop()
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


@app.get("/log/{channel}")
async def read_logs(channel: str):
    try:
        with open("{}/logs/#{}.log".format(os.getenv("DATA_FOLDER"), channel), "r") as file:
            content = file.read()
        return PlainTextResponse(content)
    except FileNotFoundError:
        return {"error": "File not found"}


@app.get("/log-file/{filename}")
async def read_logs(filename: str):
    try:
        with open("{}/logs/#{}.log".format(os.getenv("DATA_FOLDER"), filename), "r") as file:
            content = file.read()
        return PlainTextResponse(content)
    except FileNotFoundError:
        return {"error": "File not found"}


@app.get("/")
async def root():
    PlainTextResponse("Hello world!")


def irc_pre_flight_check():
    settings = read_json_file("{}/irc.json".format(os.getenv("DATA_FOLDER")))
    if not settings['server']:
        print("No IRC server set")
        sys.exit()
    if not settings['port']:
        print("No IRC port set")
        sys.exit()
    elif settings['port'] == 6697 and not settings['ssl']:
        print("Enable SSL if using 6697")
        sys.exit()
    if not settings['nick']:
        print("No IRC nick set")
        sys.exit()
    if settings['nick'] and not settings['password']:
        print("IRC nick password is not set")
    channels = read_json_file("{}/channels.json".format(os.getenv("DATA_FOLDER")))
    if not channels or not [c for c in channels if c]:
        print("No channels to join")
        sys.exit()
    else:
        channels = ["#{}".format(c.lstrip('#')) for c in channels]
    return {"server": settings['server'], "port": settings['port'], "nick": settings['nick'], "password": settings['password'], "ssl": settings['ssl'], "channels": channels}


if __name__ == "__main__":
    print("-" * 50)
    print("Simple IRC Log Web Server")
    print("-" * 50)
    irc_pre_flight_check()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("VIRTUAL_PORT")))
