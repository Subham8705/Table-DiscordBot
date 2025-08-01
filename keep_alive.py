from flask import Flask
from threading import Thread

app = Flask('')


@app.route('/')
def home():
    print("✅ Ping received — bot is still alive!")
    return "Bot is alive!"


def run():
    app.run(host='0.0.0.0', port=8080)


def keep_alive():
    t = Thread(target=run)
    t.start()
