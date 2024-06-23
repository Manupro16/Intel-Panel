import asyncio
import aiohttp
import logging
from decotools import session_manager
from typing import Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

QUEUE_MAPPING = {
    0: "Custom",
    2: "Normal",
    4: "Ranked Solo",
    6: "Ranked Duo",
    7: "Historical",
    8: "Normal 3v3",
    9: "Ranked Flex",
    14: "Normal Draft",
    16: "Dominion",
    17: "ARAM",
    25: "ARAM Co-op vs AI",
    31: "Co-op vs AI",
    32: "Co-op vs AI Intro",
    33: "Co-op vs AI Beginner",
    52: "Twisted Treeline Co-op vs AI",
    61: "Team Builder",
    65: "ARAM Ultra Rapid Fire",
    67: "Doom Bots Rank 1",
    70: "One for All",
    72: "Snowdown Showdown 1v1",
    73: "Snowdown Showdown 2v2",
    75: "Hexakill",
    76: "URF",
    78: "One for All (Mirror)",
    83: "Ultra Rapid Fire Co-op vs AI",
    91: "Doom Bots Rank 2",
    92: "Doom Bots Rank 5",
    93: "Ascension",
    96: "Hexakill Twisted Treeline",
    98: "6v6 Hexakill",
    100: "ARAM Butcher's Bridge",
    300: "Legend of the Poro King",
    310: "Nemesis",
    313: "Black Market Brawlers",
    315: "Nexus Siege",
    317: "Definitely Not Dominion",
    318: "All Random URF",
    325: "All Random Summoner's Rift",
    400: "Draft Pick",
    420: "Ranked",
    430: "Blind Pick",
    440: "Flex",
    450: "ARAM",
    460: "Dark Star Singularity",
    470: "Ranked Flex 3v3",
    600: "Blood Hunt Assassin",
    610: "Dark Star: Singularity",
    700: "Clash",
    800: "Co-op vs. AI Intermediate",
    810: "Co-op vs. AI Intro",
    820: "Co-op vs. AI Beginner",
    830: "Co-op vs. AI Intro Bot",
    840: "Co-op vs. AI Beginner Bot",
    850: "Co-op vs. AI Intermediate Bot",
    900: "URF",
    910: "Ascension",
    920: "Legend of the Poro King",
    940: "Nexus Siege",
    950: "Doom Bots Voting",
    960: "Doom Bots Standard",
    980: "Star Guardian Invasion: Normal",
    990: "Star Guardian Invasion: Onslaught",
    1000: "PROJECT: Hunters",
    1010: "Snow ARURF",
    1020: "One for All",
    1030: "Odyssey Extraction: Intro",
    1040: "Odyssey Extraction: Cadet",
    1050: "Odyssey Extraction: Crewmember",
    1060: "Odyssey Extraction: Captain",
    1070: "Odyssey Extraction: Onslaught",
    1090: "Teamfight Tactics",
    1100: "Ranked Teamfight Tactics",
    1110: "Teamfight Tactics Tutorial",
    1111: "Teamfight Tactics Test",
    1200: "Nexus Blitz",
}


def get_game_mode_from_queue(queue_id: int) -> str:
    return QUEUE_MAPPING.get(queue_id, "Unknown")


def _transform_match_data(match_data: List[Dict[str, Any]], summoner_id: str) -> List[Dict[str, Any]]:
    transformed_data = []
    for data in match_data:
        queue_id = data.get('queueId', None)
        if queue_id is not None:
            data['gameMode'] = get_game_mode_from_queue(queue_id)

        participant_info = next((identity for identity in data['participantIdentities']
                                 if identity['player']['summonerId'] == summoner_id), None)
        participant_id = participant_info['participantId'] if participant_info else None

        if participant_id:
            participant_team = next((participant['teamId'] for participant in data['participants']
                                     if participant['participantId'] == participant_id), None)
            if participant_team:
                team_win = next((team['win'] for team in data['teams'] if team['teamId'] == participant_team), 'Fail')
                data['winLoss'] = 'Victory' if team_win == 'Win' else 'Defeat'
        transformed_data.append(data)
    return transformed_data


logger = logging.getLogger(__name__)


class LCUDataRetriever:
    def __init__(self, ssl, cache):
        self.ssl = ssl
        self.cache = cache

    async def get_client_data(self):
        credentials = self.cache.get_client_credentials()
        self.cache.set('current_summoner',
                       await self.current_summoner(port=credentials.get('port'), password=credentials.get('password')))

        tasks = {
            'summoner_mastery': self.get_summoner_mastery(port=credentials.get('port'),
                                                          password=credentials.get('password')),
            'current_ranked_stats': self.get_summoner_rank_stats(port=credentials.get('port'),
                                                                 password=credentials.get('password')),
            'summoner_match_data': self.get_summoner_match_data(port=credentials.get('port'),
                                                                password=credentials.get('password')),
            'champs_data': self.get_champs_data(),

            'summoner_friends': self.get_friends_data(port=credentials.get('port'),
                                                      password=credentials.get('password'))

        }

        results = await asyncio.gather(*tasks.values())

        for name, data in zip(tasks.keys(), results):
            if isinstance(data, Exception):
                logging.error(f"Error while executing task {name}: {data}")
            else:
                self.cache.set(name, data)

    @session_manager
    async def current_summoner(self, session: aiohttp.ClientSession, port: str, password: str) -> Dict[str, Any]:
        url = f"https://127.0.0.1:{port}/lol-summoner/v1/current-summoner"
        async with session.get(url, ssl=self.ssl, auth=aiohttp.BasicAuth('riot', password=password)) as response:
            if response.status == 200:
                user_data = await response.json()
                profile_icon_url = f"https://ddragon.leagueoflegends.com/cdn/14.8.1/img/profileicon/{user_data.get('profileIconId', '')}.png"
                return {
                    "accountId": user_data.get("accountId", ""),
                    "displayName": user_data.get("displayName", ""),
                    "profileIconUrl": profile_icon_url,
                    "puuid": user_data.get("puuid", ""),
                    "summonerId": user_data.get("summonerId", ""),
                    "summonerLevel": user_data.get("summonerLevel", "")
                }
            else:
                raise ValueError(f"Unexpected response status: {response.status}")

    @session_manager
    async def get_summoner_mastery(self, session: aiohttp.ClientSession, port: str, password: str) -> List[
        Dict[str, Any]]:
        summoner_id = self.cache.get_nested('current_summoner', 'summonerId')
        url = f"https://127.0.0.1:{port}/lol-collections/v1/inventories/{summoner_id}/champion-mastery"
        async with session.get(url=url, ssl=self.ssl, auth=aiohttp.BasicAuth('riot', password=password)) as response:
            if response.status != 200:
                raise ValueError(f"Unexpected response status: {response.status}")
            mastery_log = await response.json()
            if not isinstance(mastery_log, list) or any(not isinstance(entry, dict) for entry in mastery_log):
                raise TypeError("Unexpected response content")
        return mastery_log[:3]  # Return the top 3 mastery entries

    @session_manager
    async def get_summoner_rank_stats(self, session: aiohttp.ClientSession, port: str, password: str) -> Dict[str, Any]:
        url = f"https://127.0.0.1:{port}/lol-ranked/v1/current-ranked-stats"
        async with session.get(url, ssl=self.ssl, auth=aiohttp.BasicAuth('riot', password=password)) as response:
            if response.status != 200:
                raise ValueError("Unexpected response status: {response.status}")
            rank_stats = await response.json(content_type=None)
            if not isinstance(rank_stats, dict):
                raise TypeError("Unexpected response content")

            try:
                highest_ranked_entry = rank_stats['highestRankedEntry']
                seasons = rank_stats['seasons']
                ranked_solo = seasons['RANKED_SOLO_5x5']

                data_log = {
                    "highestTier": highest_ranked_entry['highestTier'].title(),
                    "queueType": highest_ranked_entry['queueType'],
                    "division": highest_ranked_entry['division'],
                    "losses": highest_ranked_entry['losses'],
                    "wins": highest_ranked_entry['wins'],
                    "leaguePoints": highest_ranked_entry['leaguePoints'],
                    "miniSeriesProgress": highest_ranked_entry.get('miniSeriesProgress', ''),
                    "provisionalGamesRemaining": highest_ranked_entry.get('provisionalGamesRemaining', 0),
                    "highestCurrentSeasonTier": rank_stats.get('highestCurrentSeasonReachedTierSR', 'Unknown'),
                    "highestPreviousSeasonTier": rank_stats.get('highestPreviousSeasonEndTier', 'Unknown'),
                    "highestPreviousSeasonDivision": rank_stats.get('highestPreviousSeasonEndDivision', 'Unknown'),
                    "win-rate": None,  # Calculated below
                    "rank-logo": highest_ranked_entry['highestTier'].title(),
                    "current-season": ranked_solo['currentSeasonId']
                }

                total_games = highest_ranked_entry.get("wins", 0) + highest_ranked_entry.get("losses", 0)
                data_log['win-rate'] = round((highest_ranked_entry.get("wins", 0) / total_games) * 100,
                                             2) if total_games > 0 else 0.00
            except KeyError as e:
                raise KeyError(f"Expected key not found in response: {str(e)}")

        return data_log

    @session_manager
    async def get_summoner_match_data(self, session: aiohttp.ClientSession, port: str, password: str) -> List[Dict[str, Any]]:
        puuid = self.cache.get_nested('current_summoner', 'puuid')
        summoner_id = self.cache.get_nested('current_summoner', 'summonerId')
        url = f"https://127.0.0.1:{port}/lol-match-history/v1/products/lol/{puuid}/matches"
        async with session.get(url, ssl=self.ssl, auth=aiohttp.BasicAuth('riot', password)) as response:
            if response.status != 200:
                raise ValueError("Unexpected response status: {response.status}")
            match_data = await response.json()
            return _transform_match_data(match_data['games']['games'][:10],
                                         summoner_id=summoner_id)  # Latest 10 matches

    @session_manager
    async def get_champs_data(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        url = "https://ddragon.leagueoflegends.com/cdn/14.8.1/data/en_US/champion.json"
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json(content_type=None)
                if not isinstance(data, dict):
                    raise TypeError("Unexpected response content")
                return data['data']
            else:
                raise ValueError(f"Unexpected response status: {response.status}")

    @session_manager
    async def get_friends_data(self, session: aiohttp.ClientSession, port: str, password: str) -> List[Dict[str, Any]]:
        url = f"https://127.0.0.1:{port}/lol-chat/v1/friends"
        async with session.get(url, ssl=self.ssl, auth=aiohttp.BasicAuth('riot', password)) as response:
            if response.status != 200:
                raise ValueError(f"Unexpected response status: {response.status}")
            return await response.json()

    @session_manager
    async def set_lobby_match(self, session: aiohttp.ClientSession, lobby_id: int) -> None:
        payload = {"queueId": lobby_id}
        url = f"https://127.0.0.1:{self.cache.client_credentials.get('port')}/lol-lobby/v2/lobby"
        async with session.post(url, ssl=self.ssl,
                                auth=aiohttp.BasicAuth('riot', self.cache.client_credentials.get('password')),
                                json=payload) as response:
            if response.status != 200:
                response_text = await response.text()
                logger.error(f"Failed to set lobby match: {response.status} - {response_text}")

    @session_manager
    async def search_lobby(self, session: aiohttp.ClientSession) -> None:
        url = f"https://127.0.0.1:{self.cache.client_credentials.get('port')}/lol-lobby/matchmaking/search"
        async with session.post(url, ssl=self.ssl, auth=aiohttp.BasicAuth('riot', self.cache.client_credentials.get(
                'password'))) as response:
            if response.status != 200:
                response_text = await response.text()
                logger.error(f"Failed to set lobby match: {response.status} - {response_text}")

    @session_manager
    async def accept_match(self, session: aiohttp.ClientSession) -> None:
        url = f"https://127.0.0.1:{self.cache.client_credentials.get('port')}/lol-matchmaking/v1/ready-check/accept"
        async with session.post(url, ssl=self.ssl, auth=aiohttp.BasicAuth('riot', self.cache.client_credentials.get(
                'password'))) as response:
            if response.status != 200:
                response_text = await response.text()
                logger.error(f"Failed to accept match: {response.status} - {response_text}")

    @session_manager
    async def invite_friend(self, session: aiohttp.ClientSession, friend_id: int, index: int) -> Dict[str, Any]:
        try:
            payload = [{"toSummonerId": friend_id}]
            url = f"https://127.0.0.1:{self.cache.client_credentials.get('port')}/lol-lobby/v2/lobby/invitations"
            async with session.post(url, ssl=self.ssl,
                                    auth=aiohttp.BasicAuth('riot', self.cache.client_credentials.get('password')),
                                    json=payload) as response:
                if response.status == 200:
                    return {"message": "Invitation sent successfully", "index": index, "status": "success"}
                else:
                    response_text = await response.text()
                    logger.error(f"Failed to invite friend: {response.status} - {response_text}")
                    return {"message": "Failed to invite: SETUP A LOBBY FIRST", "index": index, "status": "error"}
        except Exception as e:
            logger.error(f"An error occurred while trying to invite friend: {str(e)}")
            return {"message": "An error occurred", "index": index, "status": "error"}
