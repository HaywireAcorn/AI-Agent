import os
import time
from trueforge_sdk import TrueForge
from trueforge_sdk.events import is_event_delta, merge_event_delta
from dotenv import load_dotenv

load_dotenv()

class Agent:
    def __init__(self):
        self.thinking = False
        
        self.client = TrueForge(
            base_url=os.getenv('TRUEFORGE_BASE_URL'),
            timeout=600,
        )
    
    def create_session(self, agent_name='researcher'):
        self.session = self.client.sessions.create(agent={'name': agent_name})
        print(f'Created Session: {self.session.data.id}')
        
    def create_turn_stream(self, input_content):
        events = {}
        turn_id = None
        last_event_id = None
        
        with self.client.sessions.create_turn_stream(
            session_id=self.session.data.id,
            input=[
                {
                    'type': 'user.message',
                    'content': (input_content),
                }
            ],
        ) as stream:
            for event in stream:
                last_event_id = event.id
                
                if event.type == 'thread.created':
                    print(f'\n subagent: {event.title}')
                    
                if event.type == 'model.message.delta' and event.thread_id == 'main':
                    print(event, input_content or '', end='', flush=True)
                    
                if event.type == 'turn.created':
                    turn_id = event.turn_id
                    
                if is_event_delta(event):
                    base = events.get(event.id)
                    
                    if not base is None:
                        merge_event_delta(base, event)
                        
                else:
                    events[event.id] = event
                    
                if event.type == 'turn.done' and event.state.status == 'done':
                    output = event.state.output
                    
                    print(
                        '\n\n ---brief--- \n',
                        None if output is None else output.content,
                    )
                    
    def create_turn(self, input_content='hello world'):
        created = self.client.sessions.create_turn(
            session_id=self.session.data.id,
            input=[
                {
                    'type': 'user.message',
                    'content': (input_content),
                }
            ],
        )
        
        turn = created.data
        
        while turn.state.status == 'running':
            time.sleep(0.5)
            turn = self.client.sessions.get_turn(
                session_id=self.session.data.id,
                turn_id=created.data.id
            ).data
            
        print(turn.state)
        
        return turn
                    
    def list_sessions(self):
        for session in self.client.sessions.list():
            print(session.id, session.created_at)
            
    def list_turns(self):
        for turn in self.client.sessions.list_turns(session_id=self.session.data.id):
            print(turn.id, turn.state.status)
            
            if turn.state.status == 'done' and (not turn.state.output is None):
                print(turn.state.output.content)