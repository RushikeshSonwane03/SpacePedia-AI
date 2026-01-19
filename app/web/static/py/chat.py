import asyncio
import json
from js import document, console, window
from pyodide.http import pyfetch
from pyodide.ffi import create_proxy

API_URL = "http://localhost:8000/api/v1"

class AppState:
    chat_id = None

state = AppState()

# --- API Helper ---
async def fetch_json(url, method="GET", body=None):
    headers = {"Content-Type": "application/json"}
    try:
        if body:
            body = json.dumps(body)
        response = await pyfetch(url, method=method, headers=headers, body=body)
        if not response.ok:
            console.error(f"HTTP Error: {response.status}")
            return None
        return await response.json()
    except Exception as e:
        console.error(f"Fetch failed: {e}")
        return None

# --- View Manager ---
class ViewManager:
    @staticmethod
    def show(view_id):
        views = document.querySelectorAll('.view-section')
        for view in views:
            view.classList.remove('active-view')
        
        target = document.getElementById(view_id)
        if target:
            target.classList.add('active-view')
            
        # Toggle Home Button
        btn_home = document.getElementById('btn-home')
        if btn_home:
            if view_id == 'hero-view':
                btn_home.style.display = 'none'
            else:
                btn_home.style.display = 'flex'

# --- Controllers ---
class MenuController:
    def __init__(self):
        self.btn_about = document.getElementById('btn-about')
        self.btn_chats = document.getElementById('btn-chats')
        
        self.btn_about.addEventListener('click', create_proxy(self.on_about))
        self.btn_chats.addEventListener('click', create_proxy(self.on_history))

    def on_about(self, event=None):
        ViewManager.show('about-view')
        asyncio.ensure_future(AboutController.load())

    def on_history(self, event=None):
        ViewManager.show('history-view')
        asyncio.ensure_future(HistoryController.load())

class ChatController:
    chat_history = document.getElementById('chat-history')
    user_input = document.getElementById('user-input')
    send_btn = document.getElementById('send-btn')

    @staticmethod
    def append_message(role, text, metadata=None):
        div = document.createElement('div')
        div.classList.add('message', role.lower())
        
        # Basic Formatting
        content = text.replace("**", "<strong>").replace("**", "</strong>").replace("\n", "<br>")
        div.innerHTML = content

        if role == 'Assistant' and metadata and metadata.get('confidence'):
            conf_div = document.createElement('div')
            conf_div.classList.add('confidence')
            dot = document.createElement('div')
            dot.classList.add('confidence-dot', f"confidence-{metadata['confidence'].lower()}")
            conf_div.appendChild(dot)
            conf_div.innerHTML += f"Confidence: {metadata['confidence']} • {metadata.get('reasoning', '')}"
            div.appendChild(conf_div)

        ChatController.chat_history.appendChild(div)
        ChatController.chat_history.scrollTop = ChatController.chat_history.scrollHeight

    @staticmethod
    async def create_session():
        console.log("Creating new session on backend...")
        data = await fetch_json(f"{API_URL}/chats", method="POST", body={"title": "New Session"})
        if data:
            state.chat_id = data['id']
            console.log(f"Chat ID: {state.chat_id}")
            return True
        return False

    @staticmethod
    async def init_chat():
        console.log("Initializing local chat view...")
        state.chat_id = None # No DB session yet
        ChatController.chat_history.innerHTML = "" 
        ChatController.append_message("Assistant", "Hello traveler! I'm SpacePedia AI. Ask me anything about space exploration.")
        TitleController.update_display("New Chat")

    @staticmethod
    async def  new_chat():
        ViewManager.show('chat-view')
        await ChatController.init_chat()

    @staticmethod
    async def send(event=None):
        text = ChatController.user_input.value.strip()
        if not text:
            return

        # Lazy Creation: Create session now if it doesn't exist
        if not state.chat_id:
             created = await ChatController.create_session()
             if not created:
                 ChatController.append_message('System', "Error creating chat session.")
                 return
             # Update title if creation returned one (default "New Chat" anyway)
             # But backend might accept title if we passed it. 
             # create_session passes {"title": "New Session"}.
             # TitleController.update_display("New Session") # Match backend default

        ChatController.append_message('User', text)
        ChatController.user_input.value = ''
        ChatController.user_input.disabled = True
        
        # Loading indicator
        loading_div = document.createElement('div')
        loading_div.classList.add('message', 'assistant')
        loading_div.textContent = "Thinking..."
        loading_div.id = "loading-msg"
        ChatController.chat_history.appendChild(loading_div)
        ChatController.chat_history.scrollTop = ChatController.chat_history.scrollHeight

        try:
            data = await fetch_json(f"{API_URL}/chats/{state.chat_id}/messages", method="POST", body={"content": text})
            document.getElementById('loading-msg').remove()
            if data:
                ChatController.append_message('Assistant', data['content'])
                
            # If title was "New Chat", it might have been auto-renamed by backend now.
            # We should re-fetch title or assume backend updated it?
            # Backend updates title if "New Chat".
            # Let's fetch updated chat info just in case? Or only if "New Chat".
            if TitleController.title_span.textContent in ["New Chat", "New Session"]:
                 # Fetch latest info
                 chat_info = await fetch_json(f"{API_URL}/chats/{state.chat_id}")
                 if chat_info and chat_info.get('title'):
                      TitleController.update_display(chat_info['title'])

        except Exception as e:
            console.error(str(e))
            try: document.getElementById('loading-msg').remove()
            except: pass
            ChatController.append_message('System', "Error sending message.")
        finally:
            ChatController.user_input.disabled = False
            ChatController.user_input.focus()

    @staticmethod
    def on_keypress(event):
        if event.key == "Enter":
            asyncio.ensure_future(ChatController.send())

class AboutController:
    all_data = [] # Store for filtering

    @staticmethod
    def bind_search():
        inp = document.getElementById('knowledge-search')
        if inp:
            inp.addEventListener('input', create_proxy(AboutController.on_search))

    @staticmethod
    def on_search(event):
        query = document.getElementById('knowledge-search').value.lower()
        if not query:
            AboutController.render(AboutController.all_data)
            return
        
        filtered = []
        for item in AboutController.all_data:
            if query in item['title'].lower() or query in item.get('category', '').lower():
                filtered.append(item)
        AboutController.render(filtered)

    @staticmethod
    async def load():
        container = document.getElementById('knowledge-list')
        container.innerHTML = "<p>Loading verified sources...</p>"
        
        data = await fetch_json(f"{API_URL}/meta/knowledge")
        if not data:
            container.innerHTML = "<p>No sources found.</p>"
            return

        AboutController.all_data = data
        AboutController.bind_search()
        AboutController.render(data)

    @staticmethod
    def render(data):
        container = document.getElementById('knowledge-list')
        container.innerHTML = ""
        
        # Group by Category
        categories = {}
        for item in data:
            cat = item.get('category', 'Uncategorized')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
            
        # Sort Categories
        sorted_cats = sorted(categories.keys())

        if not sorted_cats:
            container.innerHTML = "<p>No matches found.</p>"
            return

        for cat in sorted_cats:
            items = categories[cat]
            
            # Card Element
            card = document.createElement('div')
            card.className = "category-card"
            
            # Header
            header = document.createElement('div')
            header.className = "category-header"
            header.innerHTML = f"<span>{cat}</span><span style='font-size:0.8em; opacity:0.6; background:rgba(0,0,0,0.3); padding:2px 8px; border-radius:10px;'>{len(items)}</span>"
            card.appendChild(header)
            
            # List
            ul = document.createElement('ul')
            ul.className = "doc-list"
            
            for item in items:
                li = document.createElement('li')
                li.className = "doc-item"
                
                title_clean = item['title'].replace('_', ' ')
                url = item['source']
                
                li.innerHTML = f"<div style='font-weight:600; color:#fff;'>{title_clean}</div><a href='{url}' target='_blank' class='doc-link'>🔗 Source</a>"
                ul.appendChild(li)
                
            card.appendChild(ul)
            container.appendChild(card)

class HistoryController:
    @staticmethod
    async def load():
        container = document.getElementById('history-items')
        container.innerHTML = "Loading..."
        chats = await fetch_json(f"{API_URL}/chats?limit=50")
        
        container.innerHTML = ""
        if not chats:
            container.innerHTML = "<p>No matches found.</p>"
            return

        for chat in chats:
            div = document.createElement('div')
            div.classList.add('history-item')
            title = chat.get('title') or f"Chat {chat['id'][:8]}"
            
            # Format Timestamp
            # ISO: 2024-01-18T10:00:00.123456
            ts = chat.get('updated_at', chat['created_at'])
            if 'T' in ts:
                date_part, time_part = ts.split('T')
                time_part = time_part[:5] # HH:MM
                ts_display = f"{time_part} · {date_part}"
            else:
                ts_display = ts[:16]

            div.innerHTML = f"<span>{title}</span><small>{ts_display}</small>"
            
            # Click Handler
            handler = create_proxy(lambda e, cid=chat['id']: asyncio.ensure_future(HistoryController.select_chat(cid)))
            div.addEventListener('click', handler)
            container.appendChild(div)

    @staticmethod
    async def select_chat(chat_id):
        console.log(f"Switching to chat {chat_id}")
        state.chat_id = chat_id
        ViewManager.show('chat-view')
        
        # Reload chat messages
        ChatController.chat_history.innerHTML = "" 
        
        full_chat = await fetch_json(f"{API_URL}/chats/{chat_id}")
        if full_chat:
            if 'title' in full_chat:
                TitleController.update_display(full_chat['title'])
            
            if 'messages' in full_chat:
                if not full_chat['messages']:
                     ChatController.append_message("Assistant", "Welcome back! History is empty.")
                
                # Sort likely needed if not guaranteed order
                for msg in full_chat['messages']:
                    role = 'User' if msg['role'] == 'user' else 'Assistant'
                    ChatController.append_message(role, msg['content'])
        
        ChatController.user_input.disabled = False
        ChatController.user_input.focus()


class TitleController:
    wrapper = document.getElementById('chat-title-wrapper') # Class selector in HTML actually
    # Wait, HTML uses class chat-title-wrapper but inside header-left.
    # Logic:
    # 1. Click edit -> Show input, hide text.
    # 2. Input -> Debounce check.
    # 3. Enter -> Save.
    
    title_span = document.getElementById('current-chat-title')
    edit_btn = document.getElementById('edit-title-btn')
    save_btn = document.getElementById('save-title-btn') # New binding
    input_wrapper = document.querySelector('.title-input-wrapper')
    input_field = document.getElementById('title-input')
    error_span = document.getElementById('title-error')
    text_wrapper = document.querySelector('.chat-title-wrapper')

    debounce_timer = None
    is_saving = False

    @staticmethod
    def bind():
        TitleController.edit_btn.addEventListener('click', create_proxy(TitleController.start_edit))
        if TitleController.save_btn:
            # Prevent blur when clicking save button
            TitleController.save_btn.addEventListener('mousedown', create_proxy(lambda e: e.preventDefault()))
            TitleController.save_btn.addEventListener('click', create_proxy(TitleController.save_title))
        
        TitleController.input_field.addEventListener('input', create_proxy(TitleController.on_input))
        TitleController.input_field.addEventListener('keydown', create_proxy(TitleController.on_keydown))
        TitleController.input_field.addEventListener('blur', create_proxy(TitleController.save_title))

    @staticmethod
    def start_edit(event=None):
        current_title = TitleController.title_span.textContent
        TitleController.input_field.value = current_title
        
        TitleController.text_wrapper.style.display = 'none'
        TitleController.input_wrapper.style.display = 'flex'
        TitleController.input_field.focus()
        TitleController.error_span.style.display = 'none'

    @staticmethod
    def on_input(event):
        if TitleController.debounce_timer:
            window.clearTimeout(TitleController.debounce_timer)
        TitleController.debounce_timer = window.setTimeout(create_proxy(TitleController.check_duplicate), 500)

    @staticmethod
    def on_keydown(event):
        if event.key == "Enter":
            TitleController.input_field.blur() 
        elif event.key == "Escape":
            TitleController.cancel_edit()

    @staticmethod
    def cancel_edit():
        if TitleController.debounce_timer:
            window.clearTimeout(TitleController.debounce_timer)
            
        TitleController.text_wrapper.style.display = 'flex'
        TitleController.input_wrapper.style.display = 'none'
        TitleController.error_span.style.display = 'none'

    @staticmethod
    async def check_duplicate():
        # Abort if edit closed
        if TitleController.input_wrapper.style.display == 'none':
            return

        title = TitleController.input_field.value.strip()
        if not title:
            return

        # Don't check if match current
        if title == TitleController.title_span.textContent:
             TitleController.error_span.style.display = 'none'
             return

        try:
            data = await fetch_json(f"{API_URL}/chats/check-title?title={title}")
            if data and data['exists']:
                TitleController.error_span.textContent = "Title already exists"
                TitleController.error_span.style.display = 'block'
            else:
                TitleController.error_span.style.display = 'none'
        except:
            pass

    @staticmethod
    async def save_title(event=None):
        if TitleController.is_saving: return
        
        # If wrapper hidden, we already closed
        if TitleController.input_wrapper.style.display == 'none':
            return

        TitleController.is_saving = True
        
        # Clear any pending check
        if TitleController.debounce_timer:
            window.clearTimeout(TitleController.debounce_timer)

        new_title = TitleController.input_field.value.strip()
        old_title = TitleController.title_span.textContent
        
        # Revert if empty/same
        if not new_title or new_title == old_title:
             TitleController.cancel_edit()
             TitleController.is_saving = False
             return
             
        # Check explicit error state (if visible)
        if TitleController.error_span.style.display == 'block':
             TitleController.input_field.focus()
             TitleController.is_saving = False
             return

        console.log(f"Saving title: {new_title}")
        success = False
        try:
            if state.chat_id:
                 data = await fetch_json(f"{API_URL}/chats/{state.chat_id}", method="PATCH", body={"title": new_title})
                 if data:
                     success = True
                     TitleController.update_display(new_title)
            else:
                 console.log("Creating session with custom title...")
                 data = await fetch_json(f"{API_URL}/chats", method="POST", body={"title": new_title})
                 if data:
                     state.chat_id = data['id']
                     success = True
                     TitleController.update_display(new_title)
        except Exception as e:
            console.error(f"Save failed: {e}")

        if success:
             TitleController.cancel_edit()
        else:
             TitleController.error_span.textContent = "Error saving"
             TitleController.error_span.style.display = 'block'
             
        TitleController.is_saving = False

    @staticmethod
    def update_display(title):
        TitleController.title_span.textContent = title


# --- Main ---
async def main():
    menu = MenuController()
    TitleController.bind() # Bind Title Logic
    
    # Global Binds
    document.getElementById('back-to-chat-about').addEventListener('click', create_proxy(lambda e: ViewManager.show('chat-view')))
    document.getElementById('back-to-chat-history').addEventListener('click', create_proxy(lambda e: ViewManager.show('chat-view')))
    
    btn_home = document.getElementById('btn-home')
    if btn_home:
        btn_home.addEventListener('click', create_proxy(lambda e: ViewManager.show('hero-view')))

    document.getElementById('btn-new-chat').addEventListener('click', create_proxy(lambda e: asyncio.ensure_future(ChatController.new_chat())))

    document.getElementById('send-btn').addEventListener('click', create_proxy(lambda e: asyncio.ensure_future(ChatController.send(e))))
    document.getElementById('user-input').addEventListener('keypress', create_proxy(ChatController.on_keypress))

    # Hero Bindings
    btn_start = document.getElementById('btn-start-journey')
    if btn_start:
        btn_start.addEventListener('click', create_proxy(lambda e: asyncio.ensure_future(ChatController.new_chat())))

    # Auto Init - REMOVED
    # await ChatController.init_chat()

    # Ensure correct initial view state (Hides Home Button)
    ViewManager.show('hero-view')

asyncio.ensure_future(main())
