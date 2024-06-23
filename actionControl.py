import asyncio
from typing import Optional, Dict


class ActionController:
    def __init__(self, observer_manager, api_client_calls):
        self.observer_manager = observer_manager
        self.api_client_calls = api_client_calls

    def handle_calls(self, action_type: str, data: Dict[str, str], index: Optional[int] = None):
        if action_type == 'invite_friend':
            friend_id = data.get('friend_id')
            if friend_id:
                asyncio.create_task(self.invite_friend(friend_id, index))

    async def invite_friend(self, friend_id: str, index: Optional[int] = None):
        try:
            response = await self.api_client_calls.invite_friend(friend_id=friend_id, index=index)
            self.observer_manager.notify(key="update_ui", function='respond_message_friends', value=response,
                                         index=index)
        except Exception as e:
            print(f"Error inviting friend: {e}")
            self.observer_manager.notify(key="update_ui", function='respond_message_friends',
                                         value={'status': 'error', 'message': str(e), 'index': index})
