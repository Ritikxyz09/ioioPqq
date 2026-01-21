#!/usr/bin/env python3

import os
import subprocess
import telebot
import re
import psutil
import time
import shutil
import zipfile
import platform
from telebot import types
from datetime import datetime

# --- Configuration ---
BOT_TOKEN = "8487271564:AAGCRluXa85Mpaz5dli826w1fKKDSRNI_LE"
OWNER_ID = 7964730489  # The user with "Owner Power"
AUTHORIZED_USERS = []

bot = telebot.TeleBot(BOT_TOKEN)
user_working_dirs = {}
user_states = {} # 'unlimited_upload', 'waiting_cmd', etc.

# --- Power Check ---
def is_owner(user_id):
    return user_id == OWNER_ID

def is_authorized(user_id):
    return user_id in AUTHORIZED_USERS or user_id == OWNER_ID

# --- Helper Functions ---
def get_user_dir(user_id):
    if user_id not in user_working_dirs:
        user_working_dirs[user_id] = os.getcwd()
    return user_working_dirs[user_id]

def update_user_dir(user_id, new_dir):
    user_working_dirs[user_id] = new_dir

# --- UI Components (Buttons) ---
def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("📁 File Manager"),
        types.KeyboardButton("🖥️ System Stats"),
        types.KeyboardButton("📥 Unlimited Upload"),
        types.KeyboardButton("🛠️ Quick Tools"),
        types.KeyboardButton("📜 Help"),
        types.KeyboardButton("🛑 Stop Mode")
    )
    return markup

def file_manager_markup(directory):
    markup = types.InlineKeyboardMarkup(row_width=2)
    try:
        items = sorted(os.listdir(directory))
        # Show first 10 items to keep it clean
        for item in items[:10]:
            path = os.path.join(directory, item)
            icon = "📁" if os.path.isdir(path) else "📄"
            callback = f"dir:{item}" if os.path.isdir(path) else f"file:{item}"
            markup.add(types.InlineKeyboardButton(f"{icon} {item}", callback_data=callback))
        
        markup.add(
            types.InlineKeyboardButton("⬅️ Parent Dir", callback_data="dir:.."),
            types.InlineKeyboardButton("🔄 Refresh", callback_data="refresh_ls")
        )
        return markup
    except:
        return None

def tools_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🌐 Public IP", callback_data="tool:ip"),
        types.InlineKeyboardButton("🔍 Process List", callback_data="tool:ps"),
        types.InlineKeyboardButton("🧹 Clear Temp", callback_data="tool:clear"),
        types.InlineKeyboardButton("🛡️ Auth Users", callback_data="tool:users")
    )
    return markup

# --- Animation ---
def animate_action(chat_id, message_id, text):
    frames = ["⚡", "🚀", "💎", "🔥", "👑"]
    for frame in frames:
        try:
            bot.edit_message_text(f"{frame} *{text}* {frame}", chat_id, message_id, parse_mode="Markdown")
            time.sleep(0.2)
        except: break

# --- Core Logic ---
def execute_owner_command(command, user_id):
    working_dir = get_user_dir(user_id)
    
    # Custom Power Commands
    if command == "whoami":
        return f"👑 *Owner:* `{platform.node()}`\n👤 *User:* `{os.getlogin()}`"
    
    try:
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=working_dir
        )
        stdout, stderr = process.communicate(timeout=30)
        if process.returncode == 0:
            return f"✅ *Success:*\n```\n{stdout.strip() or 'No output'}\n```"
        else:
            return f"❌ *Error:*\n`{stderr.strip()}`"
    except Exception as e:
        return f"💥 *Crash:* `{str(e)}`"

# --- Handlers ---
@bot.message_handler(commands=['start'])
def start_power(message):
    if not is_authorized(message.from_user.id): return
    welcome = (
        "👑 *WELCOME OWNER* 👑\n\n"
        "Your terminal is now upgraded with **Owner Power**.\n"
        "Use the buttons below to control the server."
    )
    bot.send_message(message.chat.id, welcome, reply_markup=main_menu_markup(), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📁 File Manager")
def btn_files(message):
    if not is_authorized(message.from_user.id): return
    wdir = get_user_dir(message.from_user.id)
    bot.send_message(message.chat.id, f"📂 *Current Path:* `{wdir}`", 
                     reply_markup=file_manager_markup(wdir), parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🖥️ System Stats")
def btn_stats(message):
    if not is_authorized(message.from_user.id): return
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    stats = (
        "📊 *OWNER DASHBOARD*\n\n"
        f"🔥 *CPU:* {psutil.cpu_percent()}% \n"
        f"🧠 *RAM:* {mem.percent}% ({mem.used//1048576}MB / {mem.total//1048576}MB)\n"
        f"💾 *DISK:* {disk.percent}% \n"
        f"⏰ *TIME:* {datetime.now().strftime('%H:%M:%S')}"
    )
    bot.reply_to(message, stats, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📥 Unlimited Upload")
def btn_upload(message):
    if not is_authorized(message.from_user.id): return
    user_states[message.from_user.id] = 'unlimited_upload'
    bot.reply_to(message, "📥 *UNLIMITED UPLOAD ACTIVE*\n\nSend any number of files. Send '🛑 Stop Mode' to finish.", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🛑 Stop Mode")
def btn_stop(message):
    user_id = message.from_user.id
    if user_id in user_states:
        del user_states[user_id]
        bot.reply_to(message, "✅ *All special modes disabled.*", parse_mode="Markdown")
    else:
        bot.reply_to(message, "ℹ️ No active modes.")

@bot.message_handler(func=lambda m: m.text == "🛠️ Quick Tools")
def btn_tools(message):
    if not is_authorized(message.from_user.id): return
    bot.send_message(message.chat.id, "🛠️ *Owner Toolbox:*", reply_markup=tools_markup(), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    if not is_authorized(user_id): return
    
    if call.data.startswith("dir:"):
        folder = call.data.split(":")[1]
        current = get_user_dir(user_id)
        new_path = os.path.abspath(os.path.join(current, folder))
        update_user_dir(user_id, new_path)
        bot.edit_message_text(f"📂 *Path:* `{new_path}`", call.message.chat.id, call.message.message_id, 
                             reply_markup=file_manager_markup(new_path), parse_mode="Markdown")
    
    elif call.data.startswith("file:"):
        fname = call.data.split(":")[1]
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📥 Download", callback_data=f"dl:{fname}"),
                   types.InlineKeyboardButton("🗑️ Delete", callback_data=f"del:{fname}"))
        bot.send_message(call.message.chat.id, f"📄 *File:* `{fname}`", reply_markup=markup, parse_mode="Markdown")

    elif call.data.startswith("dl:"):
        fname = call.data.split(":")[1]
        path = os.path.join(get_user_dir(user_id), fname)
        with open(path, 'rb') as f: bot.send_document(call.message.chat.id, f)

    elif call.data == "tool:ip":
        ip = subprocess.getoutput("curl -s ifconfig.me")
        bot.answer_callback_query(call.id, f"IP: {ip}", show_alert=True)

@bot.message_handler(content_types=['document', 'photo', 'audio', 'video'])
def handle_files(message):
    user_id = message.from_user.id
    if not is_authorized(user_id): return
    if user_states.get(user_id) != 'unlimited_upload':
        bot.reply_to(message, "❌ Enable '📥 Unlimited Upload' first!")
        return
    
    file_id = None
    name = "file"
    if message.document: 
        file_id = message.document.file_id
        name = message.document.file_name
    elif message.photo: 
        file_id = message.photo[-1].file_id
        name = f"img_{int(time.time())}.jpg"
    
    if file_id:
        info = bot.get_file(file_id)
        down = bot.download_file(info.file_path)
        with open(os.path.join(get_user_dir(user_id), name), 'wb') as f: f.write(down)
        bot.reply_to(message, f"✅ *Saved:* `{name}`", parse_mode="Markdown")

@bot.message_handler(func=lambda m: True)
def handle_text(message):
    if not is_authorized(message.from_user.id): return
    if user_states.get(message.from_user.id) == 'unlimited_upload': return
    
    cmd = message.text
    status = bot.reply_to(message, "⚡ *Executing...*")
    animate_action(message.chat.id, status.message_id, "POWER RUN")
    
    res = execute_owner_command(cmd, message.from_user.id)
    if len(res) > 4000:
        bot.send_message(message.chat.id, "📦 Output too large, sending as file...")
        with open("output.txt", "w") as f: f.write(res)
        with open("output.txt", "rb") as f: bot.send_document(message.chat.id, f)
    else:
        bot.edit_message_text(res, message.chat.id, status.message_id, parse_mode="Markdown")

if __name__ == "__main__":
    print("💎 OWNER EDITION RUNNING...")
    bot.infinity_polling()
