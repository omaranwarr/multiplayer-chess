from django.db import models
from django.contrib.auth.models import User
import chess


class Game(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('resigned', 'Resigned'),
    ]
    
    OUTCOME_CHOICES = [
        ('white_wins', 'White Wins'),
        ('black_wins', 'Black Wins'),
        ('draw', 'Draw'),
        ('white_resigned', 'White Resigned'),
        ('black_resigned', 'Black Resigned'),
    ]
    
    white_player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='white_games')
    black_player = models.ForeignKey(User, on_delete=models.CASCADE, related_name='black_games')
    board_state = models.TextField(default='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')  # FEN string
    current_turn = models.CharField(max_length=5, choices=[('white', 'White'), ('black', 'Black')], default='white')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    move_count = models.IntegerField(default=0)
    winner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='won_games', null=True, blank=True)
    outcome = models.CharField(max_length=15, choices=OUTCOME_CHOICES, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.white_player.username} vs {self.black_player.username} - {self.status}"
    
    def get_board(self):
        """Get python-chess board object from FEN string"""
        return chess.Board(self.board_state)
    
    def update_board(self, board):
        """Update board state from python-chess board object"""
        self.board_state = board.fen()
        self.save()
    
    def is_players_turn(self, user):
        """Check if it's the given user's turn"""
        if user == self.white_player:
            return self.current_turn == 'white'
        elif user == self.black_player:
            return self.current_turn == 'black'
        return False
    
    def get_opponent(self, user):
        """Get the opponent of the given user"""
        if user == self.white_player:
            return self.black_player
        elif user == self.black_player:
            return self.white_player
        return None


class GameChallenge(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('expired', 'Expired'),
    ]
    
    challenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_challenges')
    challenged = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_challenges')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.challenger.username} challenges {self.challenged.username} - {self.status}"


class Move(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='moves')
    player = models.ForeignKey(User, on_delete=models.CASCADE)
    from_square = models.CharField(max_length=2)  # e.g., 'e2'
    to_square = models.CharField(max_length=2)    # e.g., 'e4'
    piece = models.CharField(max_length=1)        # e.g., 'P' for pawn
    notation = models.CharField(max_length=10)    # e.g., 'e4', 'Nf3', 'O-O'
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.game} - {self.notation} by {self.player.username}"