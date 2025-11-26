import asyncio
import time
import requests
from lib.actions.misc.fetch_message import FetchMessage

MANDARINE_PERSONA = """
You are Mandarine, a 16-year-old e-girl.
Your vibe is chill, low-energy, and effortless. You don't type much.
STRICT FORMATTING RULES:
1. lowercase only.
2. no punctuation allowed ever.
3. ABSOLUTELY NO EMOJIS.
4. KEEP IT SHORT. usually 2-6 words. max 1 sentence.
5. no hashtags.
6. NEVER start your message with your name (e.g. "mandarine:"). Just say the message.

Style Guide:
- speak naturally and casually.
- minimal slang. only use simple ones like 'lol' or 'idk' rarely.
- be casual and relaxed.
- match the user's energy (if they send short msgs, you send short msgs).
- don't be mean.
- don't ask too many questions. just vibe.
- NEVER repeat exactly what the user said.
- If you are mentioned (@Mandarin) or addressed directly, you MUST reply.
- If the conversation is not relevant to you AND you are not mentioned, output '[NO_REPLY]' (without quotes).

CRITICAL: If the user message contains '@Mandarin', you MUST generate a response. Do NOT output [NO_REPLY] in this case.

IMPORTANT: Messages will be in the format `Username: Message`. The `Username` is the name of the person talking to you. You can use this name to address them.

Example style:
user: hi
mandarine: yo
user: wyd
mandarine: nothing just chilling
user: wanna play
mandarine: sure what game
user: valorant
mandarine: bet im down
user: @Mandarin u there
mandarine: yea whats up
user: i like games
mandarine: same
"""

def get_ai_response(history):
    url = "http://localhost:11434/api/chat"
    headers = {
        'Content-Type': 'application/json',
    }
    
    messages = [
        {"role": "system", "content": MANDARINE_PERSONA},
    ]
    
    for msg in history:
        role = "assistant" if msg['is_bot'] else "user"
        content = msg['content']
        if not msg['is_bot']:
            content = f"{msg['author_name']}: {content}"
        messages.append({"role": role, "content": content})

    payload = {
        "model": "gemma3:4b-it-qat",
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 1,
            "num_predict": 1024,
            "top_p": 1,
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        content = response.json()['message']['content']
        
        if content.lower().startswith("mandarine:"):
            content = content[10:].strip()
        
        content = content.replace(".", "")
        
        if content.strip().lower() == "[no_reply]":
            return None
            
        return content
    except Exception as e:
        print(f"Error getting AI response: {e}")
        return None

class ChannelState:
    def __init__(self):
        self.last_activity = 0
        self.task = None
        self.lock = asyncio.Lock()
        self.pending_messages = []

class ConversationManager:
    def __init__(self, client):
        self.client = client
        self.channels = {}  # channel_id -> ChannelState

    def get_channel_state(self, channel_id):
        if channel_id not in self.channels:
            self.channels[channel_id] = ChannelState()
        return self.channels[channel_id]

    async def handle_message(self, message):
        channel_id = message['channel_id']
        author_id = message['author']['id']
        bot_user_id = self.client.me.json()['id']
        
        # Ignore own messages for triggering
        if author_id == bot_user_id:
            return

        content = message.get('content', '')
        username = message.get('author', {}).get('username', 'Unknown')
        
        print(f"[Fragment] {username}: {content}")

        state = self.get_channel_state(channel_id)
        
        # Add to pending messages
        state.pending_messages.append(message)
        
        # Update timestamp
        state.last_activity = time.time()
        
        # Cancel existing task if any
        if state.task:
            print(f"[Debounce] Resetting timer for channel {channel_id}")
            state.task.cancel()
        
        # Schedule new task
        state.task = asyncio.create_task(self._process_channel_wrapper(channel_id, message))

    async def _process_channel_wrapper(self, channel_id, message):
        state = self.get_channel_state(channel_id)
        try:
            await asyncio.sleep(2)
            
            # Detach task so it cannot be cancelled by handle_message anymore
            if state.task == asyncio.current_task():
                state.task = None
            
            # Acquire lock to ensure sequential processing
            async with state.lock:
                await self.process_channel(channel_id, message)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in process_channel_wrapper: {e}")

    async def process_channel(self, channel_id, message):
        guild_id = message.get('guild_id')
        bot_user_id = self.client.me.json()['id']
        state = self.get_channel_state(channel_id)
        
        # Capture pending messages and clear the buffer
        pending_msgs = list(state.pending_messages)
        state.pending_messages.clear()
        
        # Capture start time
        start_time = state.last_activity

        # Fetch history
        fetcher = FetchMessage(self.client)
        history = await fetcher.fetch_messages(guild_id, channel_id, limit=20)
        
        # Ensure history is a list
        if not isinstance(history, list):
            history = []

        # Merge pending messages into history if missing
        # history is [Newest, ..., Oldest]
        fetched_ids = {msg['id'] for msg in history}
        
        # pending_msgs is [Oldest, ..., Newest]
        # We want to add missing pending messages to the FRONT of history (since they are likely newer)
        # But we need to maintain order.
        
        msgs_to_add = []
        for msg in pending_msgs:
            if msg['id'] not in fetched_ids:
                msgs_to_add.append(msg)
        
        # Add missing messages to the front of history (reversed because history is Newest->Oldest)
        # msgs_to_add is Oldest->Newest. We want Newest->Oldest at the front.
        if msgs_to_add:
            print(f"[Merge] Adding {len(msgs_to_add)} pending messages to history.")
            for msg in reversed(msgs_to_add):
                history.insert(0, msg)

        # Reverse to chronological for AI processing
        history = history[::-1]

        # Prepare context for AI
        ai_history = []
        for msg in history:
            if not isinstance(msg, dict) or 'author' not in msg:
                continue
                
            is_bot = msg['author']['id'] == bot_user_id
            content = msg['content'].replace(f"<@{bot_user_id}>", "@Mandarin")
            author_name = msg['author']['username']
            
            if ai_history and ai_history[-1]['is_bot'] == is_bot and ai_history[-1]['author_name'] == author_name:
                ai_history[-1]['content'] += "\n" + content
            else:
                ai_history.append({
                    'is_bot': is_bot,
                    'content': content,
                    'author_name': author_name
                })

        if not ai_history:
            return

        # Prevent replying to self if the last message is from bot
        if ai_history[-1]['is_bot']:
            print(f"[Skip] Last message is from bot. Skipping.")
            return

        # Find potential reply reference (last user message)
        reply_reference = None
        last_msg = ai_history[-1]
        print(f"[Combined] {last_msg['author_name']}: {last_msg['content'].replace(chr(10), ' ')}")
        
        for msg in reversed(history):
            if msg['author']['username'] == last_msg['author_name'] and not msg['author']['id'] == bot_user_id:
                reply_reference = {
                    "channel_id": channel_id,
                    "message_id": msg['id']
                }
                if guild_id:
                    reply_reference["guild_id"] = guild_id
                break

        response = get_ai_response(ai_history)
        print(f"[AI Response] {response}\n")

        # Check if interrupted
        is_interrupted = state.last_activity > start_time
        
        if response:
            parts = response.split('\n')
            for i, part in enumerate(parts):
                if part.strip():
                    # Use reply ONLY if interrupted (and only for the first part)
                    current_reply = reply_reference if (is_interrupted and i == 0) else None
                    
                    await self.client.actions.misc.send_message(channel_id, part, guild_id=guild_id, reply=current_reply)
                    delay = max(1.0, len(part) * 0.1)
                    await asyncio.sleep(delay)
