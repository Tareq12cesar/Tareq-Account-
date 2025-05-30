from flask import Flask
import threading

app = Flask(__name__)

BOT_TOKEN = "7933020801:AAHaBEa43nikjSSNj_qKZ0L27r3ooJV6UDI"
CHANNEL_USERNAME = "@Mobile_Legend_ir"

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run).start()

# ادامه کد بات اینجا...
