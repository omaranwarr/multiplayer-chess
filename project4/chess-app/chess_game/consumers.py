from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.db.models import Q
from django.contrib.sessions.models import Session
from django.utils.timezone import now
from django.contrib.auth.models import User

from .models import Game, GameChallenge
from .serializers import UserSerializer, GameSerializer, GameChallengeSerializer, BoardStateSerializer
from .views import get_logged_in_users_excluding_current, get_active_game, board_to_dict


class LobbyConsumer(AsyncJsonWebsocketConsumer):
    group_name = "lobby"

    async def connect(self):
        user = self.scope.get("user")
        if user is None or user.is_anonymous:
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def lobby_refresh(self, event):
        # send lobby data update
        user = self.scope.get("user")
        if user and not user.is_anonymous:
            lobby_data = await self._get_lobby_data(user)
            await self.send_json({
                "action": "lobby_refresh",
                "data": lobby_data
            })
    
    @database_sync_to_async
    def _get_lobby_data(self, user):
        # get lobby data for the user
        class MockRequest:
            def __init__(self, user):
                self.user = user
        
        mock_request = MockRequest(user)
        available_players = get_logged_in_users_excluding_current(mock_request)
        available_players = [u for u in available_players if not get_active_game(u)]
        available_players_data = UserSerializer(available_players, many=True).data
        
        pending_challenges = GameChallenge.objects.filter(
            challenged=user,
            status='pending'
        )
        pending_challenges_data = GameChallengeSerializer(pending_challenges, many=True).data
        
        user_games = Game.objects.filter(
            Q(white_player=user) | Q(black_player=user),
            status__in=['completed', 'resigned']
        ).order_by('-updated_at')[:10]
        game_history_data = GameSerializer(user_games, many=True).data
        
        return {
            "available_players": available_players_data,
            "pending_challenges": pending_challenges_data,
            "game_history": game_history_data
        }


class GameConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if user is None or user.is_anonymous:
            await self.close()
            return

        self.game_id = self.scope["url_route"]["kwargs"]["game_id"]
        self.group_name = f"game_{self.game_id}"

        if not await self._user_in_game(user.id, self.game_id):
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def game_refresh(self, event):
        # send game state update
        user = self.scope.get("user")
        if user and not user.is_anonymous:
            game_data = await self._get_game_data(user, self.game_id)
            if game_data:
                await self.send_json({
                    "action": "game_refresh",
                    "data": game_data
                })
    
    @database_sync_to_async
    def _get_game_data(self, user, game_id):
        # get game data for the user
        try:
            game = Game.objects.filter(
                id=game_id
            ).filter(
                Q(white_player=user) | Q(black_player=user)
            ).get()
            
            game_serializer = GameSerializer(game)
            game_data = game_serializer.data
            
            board = game.get_board()
            board_dict = board_to_dict(board, user, game)
            is_my_turn = game.is_players_turn(user)
            is_game_over = board.is_game_over()
            result = None
            
            if is_game_over:
                if board.is_checkmate():
                    winner = 'Black' if board.turn else 'White'
                    result = f'{winner} wins by checkmate!'
                elif board.is_stalemate():
                    result = 'Draw by stalemate!'
                elif board.is_insufficient_material():
                    result = 'Draw by insufficient material!'
            
            board_state_data = {
                'board_dict': board_dict,
                'current_turn': game.current_turn,
                'is_my_turn': is_my_turn,
                'is_game_over': is_game_over,
                'result': result
            }
            
            return {
                "game": game_data,
                "board_state": board_state_data
            }
        except Game.DoesNotExist:
            return None

    @database_sync_to_async
    def _user_in_game(self, user_id, game_id):
        return Game.objects.filter(
            Q(id=game_id),
            Q(white_player_id=user_id) | Q(black_player_id=user_id),
        ).exists()

