from nicegui import ui, app, run
from main import Agent
import asyncio
import main

### VARIABLES ###
ai_agent_models = {
    'ra': 'researcher',
}

### METHODS ###
def initialize_storage():
    app.storage.client['ai_agent'] = Agent()
    app.storage.client['ai_agent'].create_session()
    app.storage.user.clear()
    app.storage.user['chat_streams'] = {}
    app.storage.user['current_chat_stream'] = None
    
@ui.refreshable
def render_chat_stream():
    with ui.scroll_area() as sa:
        with ui.column().classes('w-full'):
            if app.storage.user['chat_streams']:
                for owner, message in app.storage.user['chat_streams'][app.storage.user['current_chat_stream']]:
                    ui.space()
                    
                    with ui.card().classes('w-full').props('flat bordered'):
                        if owner == 'user':
                            ui.markdown(message).classes('w-full text-right')
                        elif owner == 'agent':
                            ui.markdown(message).classes('w-full')
                        else:
                            ui.label(message).classes('w-full text-center')
                            
                if app.storage.client['ai_agent'].thinking:
                    with ui.skeleton().classes('w-full'):
                        ui.label('Thinking...')
                        
    sa.scroll_to(percent=1.0)
    
def set_current_render_chat_stream(chat_stream: str):
    app.storage.user['current_chat_stream'] = chat_stream
    render_chat_stream.refresh()
    render_left_drawer.refresh()
    
    print(f'Current Chat Stream: {app.storage.user['current_chat_stream']}')
    
async def add_new_chat_message(owner='user', content='Hello World'):
    if not app.storage.user['current_chat_stream'] or not app.storage.user['chat_streams']:
        add_new_chat_stream(content[:15])
        
    app.storage.user['chat_streams'][app.storage.user['current_chat_stream']].append((owner, content))
    app.storage.client['ai_agent'].thinking = True
    
    render_chat_stream.refresh()
    
    return_message = await run.io_bound(app.storage.client['ai_agent'].create_turn, content)
    return_message = return_message.state.output.content
    
    app.storage.client['ai_agent'].thinking = False
    
    app.storage.user['chat_streams'][app.storage.user['current_chat_stream']].append(('agent', return_message))
    
    render_chat_stream.refresh()
    
    print('Added New Chat Message')

@ui.refreshable
def render_left_drawer():
    try:
        for chat_label in app.storage.user['chat_streams'].keys():
            ui.button(chat_label, on_click=lambda: set_current_render_chat_stream(chat_label))
    except:
        print('Left Drawer Awaiting Storage')
        
def add_new_chat_stream(stream_name: str):
    if not stream_name in app.storage.user['chat_streams']:
        app.storage.user['chat_streams'][stream_name] = []
        app.storage.user['current_chat_stream'] = stream_name
        render_left_drawer.refresh()
        
        print(f'Added New Chat Stream: {stream_name}')

### PAGES ###
def page_layout():
    with ui.header():
        ui.button(icon='menu', on_click=lambda: ld.toggle())
    
    with ui.left_drawer(value=False, top_corner=True, bottom_corner=True, elevated=True, bordered=True) as ld:
        ui.button('Add New Chat', on_click=lambda: add_new_chat_stream('New Chat'))
        render_left_drawer()
    
def chatbox():
    with ui.column().classes('w-full items-center'):
        render_chat_stream()
        
        text_input = ui.input(
            placeholder='Start Typing to chat',
        ).classes('w-[80%]')
        
        with ui.row().classes('inline-items items-center'):
            ui.label('AI Model: ')
            
            agent_model_input = ui.select(
                options=ai_agent_models,
                with_input=True,
            ).classes('w-40')
        
        text_input.on('keydown.enter', lambda e: add_new_chat_message(content=text_input.value))
        text_input.on('keydown.enter', lambda e: text_input.set_value(''))
        
### MAIN ###
@ui.page('/')
@ui.page('/{_:path}')
def index():
    initialize_storage()
    
    page_layout()
    
    page_control = ui.sub_pages(
        {
            '/': chatbox,
        }
    ).classes('w-full')
    
ui.run(storage_secret='sts-123abc')