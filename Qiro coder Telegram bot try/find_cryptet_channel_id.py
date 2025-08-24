#!/usr/bin/env python3
"""
Script to find the Chat ID of @cryptet_com channel
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def find_cryptet_channel_id():
    """Find the Chat ID of @cryptet_com channel."""
    
    try:
        from telethon import TelegramClient
        
        api_id = int(os.getenv("TELEGRAM_API_ID"))
        api_hash = os.getenv("TELEGRAM_API_HASH") 
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        
        print("🔍 CRYPTET CHANNEL ID FINDER")
        print("=" * 50)
        print("📡 Connecting to Telegram...")
        
        client = TelegramClient("cryptet_finder_session", api_id, api_hash)
        await client.start(bot_token=bot_token)
        
        # Try to get the @cryptet_com entity
        channel_username = "cryptet_com"
        
        try:
            entity = await client.get_entity(channel_username)
            chat_id = entity.id
            
            # For channels, the ID needs to be negative and prefixed with -100
            if hasattr(entity, 'broadcast') and entity.broadcast:
                # It's a channel
                formatted_id = f"-100{chat_id}"
            else:
                # It's a group or other
                formatted_id = f"-{chat_id}" if chat_id > 0 else str(chat_id)
            
            print(f"✅ Found @{channel_username}!")
            print(f"📋 Details:")
            print(f"   Title: {getattr(entity, 'title', 'N/A')}")
            print(f"   Raw ID: {chat_id}")
            print(f"   Formatted ID: {formatted_id}")
            print(f"   Type: {'Channel' if hasattr(entity, 'broadcast') and entity.broadcast else 'Group'}")
            print()
            print(f"🎯 Use this ID in .env:")
            print(f"   MONITORED_CHAT_IDS=-2299206473,{formatted_id}")
            
            return formatted_id
            
        except Exception as e:
            print(f"❌ Could not find @{channel_username}: {e}")
            print()
            print("💡 Alternatives to try:")
            print("   1. Make sure the bot has access to the channel")
            print("   2. Try with different username format")
            print("   3. Get the ID manually by forwarding a message")
            return None
            
        finally:
            await client.disconnect()
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(find_cryptet_channel_id())