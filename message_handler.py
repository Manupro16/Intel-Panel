import logging
import json
from typing import Any, Dict, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MessageHandler:
    def __init__(self, cache, observer_manager):
        self.cache = cache
        self.observer_manager = observer_manager

    async def handle_message(self, message: str) -> Optional[None]:
        if not message:
            logging.warning("Received an empty message.")
            return None

        try:
            data = json.loads(message)
            opcode = data[0]
            event_data = data[2] if len(data) > 2 else None

            if opcode == 8 and event_data:  # Event message
                uri = event_data.get("uri", "")
                if uri == "/lol-summoner/v1/current-summoner":
                    self.handle_summoner_update(event_data)
                elif uri == "/lol-ranked/v1/current-ranked-stats":
                    self.handle_ranked_stats(event_data)
                elif uri.startswith("/lol-collections/v1/inventories/local-player/champion-mastery-score"):
                    self.handle_champion_mastery(event_data)

        except json.JSONDecodeError as e:
            logging.error(f"Failed to decode JSON from message: {message}. Error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in handle_message: {e}", exc_info=True)

    def handle_summoner_update(self, event_data: Dict[str, Any]) -> None:
        try:
            summoner_info = event_data['data']
            profile_icon_url = f"https://ddragon.leagueoflegends.com/cdn/14.8.1/img/profileicon/{summoner_info.get('profileIconId', '')}.png"

            summoner_data = {
                "accountId": summoner_info.get("accountId", ""),
                "displayName": summoner_info.get("displayName", ""),
                "profileIconUrl": profile_icon_url,
                "puuid": summoner_info.get("puuid", ""),
                "summonerId": summoner_info.get("summonerId", ""),
                "summonerLevel": summoner_info.get("summonerLevel", "")
            }
            self.cache.update("current_summoner", summoner_data)
            logging.info(f"Updated summoner data via WebSocket: {summoner_data}")
        except KeyError as e:
            logging.error(f"Key error in handle_summoner_update: missing {e} in event_data")
        except Exception as e:
            logging.error(f"Unexpected error in handle_summoner_update: {e}", exc_info=True)

    def handle_ranked_stats(self, event_data: Dict[str, Any]) -> None:
        try:
            self.cache.update("current_ranked_stats", event_data)
            logging.info(f"Updated ranked stats via WebSocket: {event_data}")
        except Exception as e:
            logging.error(f"Unexpected error in handle_ranked_stats: {e}", exc_info=True)

    def handle_champion_mastery(self, event_data: Dict[str, Any]) -> None:
        try:
            self.cache.update("summoner_mastery", event_data[:3])  # Limit to first 3 entries
            logging.info(f"Updated champion mastery via WebSocket: {event_data[:3]}")
        except Exception as e:
            logging.error(f"Unexpected error in handle_champion_mastery: {e}", exc_info=True)
