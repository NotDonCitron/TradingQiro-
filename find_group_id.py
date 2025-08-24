#!/usr/bin/env python3
"""
Script to find the correct Telegram group ID after bot is added
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def extract_chat_info(update):
    """Extrahiere Chat-Informationen aus einem Update."""
    chat = None
    message_text = "N/A"
    
    # Handle different update types
    if 'message' in update:
        message = update['message']
        chat = message['chat']
        message_text = message.get('text', 'N/A')
    elif 'channel_post' in update:
        message = update['channel_post']
        chat = message['chat']
        message_text = message.get('text', 'N/A')
    elif 'my_chat_member' in update:
        member_update = update['my_chat_member']
        chat = member_update['chat']
        new_status = member_update.get('new_chat_member', {}).get('status', 'unknown')
        message_text = "Bot status changed: {}".format(new_status)
    
    return chat, message_text

def process_chat_update(chat, message_text):
    """Verarbeite ein Chat-Update und prüfe auf Gruppen."""
    if not chat:
        return False
        
    chat_id = chat['id']
    chat_type = chat['type']
    chat_title = chat.get('title', chat.get('first_name', 'N/A'))
    
    print("Chat ID: {}".format(chat_id))
    print("Type: {}".format(chat_type))
    print("Title: {}".format(chat_title))
    print("Message: {}...".format(str(message_text)[:50]))
    print("-" * 30)
    
    # If it's a group/supergroup, suggest this ID
    if chat_type in ['group', 'supergroup']:
        print("✅ FOUND GROUP: {}".format(chat_title))
        print("🎯 Use this ID in .env: {}".format(chat_id))
        print("   OWN_GROUP_CHAT_ID={}".format(chat_id))
        print()
        return True
    
    return False

def print_no_groups_help():
    """Zeige Hilfe wenn keine Gruppen gefunden wurden."""
    print("🔍 No groups found in recent updates")
    print()
    print("💡 Please do the following:")
    print("   1. Make sure the bot is added to your group")
    print("   2. Send a message in the group (e.g., 'Hello Bot!')")
    print("   3. Wait a few seconds and run this script again")
    print("   4. If still not working, try removing and re-adding the bot")

def print_no_updates_help():
    """Zeige Hilfe wenn keine Updates gefunden wurden."""
    print("📭 No recent updates found")
    print()
    print("📝 To generate updates:")
    print("   1. Add bot to your group")
    print("   2. Send '/start' or any message in the group")
    print("   3. Run this script again")

def find_group_id():
    """Find the correct group ID using Telegram Bot API."""
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env")
        return
    
    print("🔍 TELEGRAM GROUP ID FINDER")
    print("=" * 50)
    print("🤖 Bot Token: {}...".format(bot_token[:10]))
    print()
    
    # Get updates from Telegram (with offset to get more)
    url = "https://api.telegram.org/bot{}/getUpdates?limit=100".format(bot_token)
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data['ok'] and data['result']:
                print("📥 Recent updates found:")
                print("-" * 30)
                
                group_found = False
                
                for update in data['result']:
                    chat, message_text = extract_chat_info(update)
                    if process_chat_update(chat, message_text):
                        group_found = True
                
                if not group_found:
                    print_no_groups_help()
            else:
                print_no_updates_help()
        else:
            print("❌ API Error {}: {}".format(response.status_code, response.text))
            
    except Exception as e:
        print("❌ Error: {}".format(e))

if __name__ == "__main__":
    find_group_id()