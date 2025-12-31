from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Game, GameChallenge, Move


class UserSerializer(serializers.ModelSerializer):
    # minimal user serializer for player lists
    class Meta:
        model = User
        fields = ['id', 'username']
        read_only_fields = ['id', 'username']


class MoveSerializer(serializers.ModelSerializer):
    # serializer for chess moves
    player = UserSerializer(read_only=True)
    
    class Meta:
        model = Move
        fields = ['id', 'game', 'player', 'from_square', 'to_square', 'piece', 'notation', 'timestamp']
        read_only_fields = ['id', 'player', 'timestamp']


class GameSerializer(serializers.ModelSerializer):
    # full game state serializer
    white_player = UserSerializer(read_only=True)
    black_player = UserSerializer(read_only=True)
    winner = UserSerializer(read_only=True)
    moves = MoveSerializer(many=True, read_only=True)
    
    class Meta:
        model = Game
        fields = [
            'id', 'white_player', 'black_player', 'board_state', 'current_turn',
            'status', 'move_count', 'winner', 'outcome', 'created_at', 'updated_at', 'moves'
        ]
        read_only_fields = [
            'id', 'white_player', 'black_player', 'status', 'move_count',
            'winner', 'outcome', 'created_at', 'updated_at', 'moves'
        ]


class GameChallengeSerializer(serializers.ModelSerializer):
    # serializer for game challenges
    challenger = UserSerializer(read_only=True)
    challenged = UserSerializer(read_only=True)
    
    class Meta:
        model = GameChallenge
        fields = ['id', 'challenger', 'challenged', 'status', 'created_at']
        read_only_fields = ['id', 'challenger', 'challenged', 'status', 'created_at']


class BoardStateSerializer(serializers.Serializer):
    # serializer for board state representation
    board_dict = serializers.DictField()
    current_turn = serializers.CharField()
    is_my_turn = serializers.BooleanField()
    is_game_over = serializers.BooleanField()
    result = serializers.CharField(required=False, allow_null=True)

