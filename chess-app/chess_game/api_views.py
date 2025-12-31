from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.db import models
from django.db.models import Q
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
import chess

from .models import Game, GameChallenge, Move
from .serializers import (
    UserSerializer, GameSerializer, GameChallengeSerializer,
    MoveSerializer, BoardStateSerializer
)
from .views import (
    get_logged_in_users_excluding_current, get_active_game,
    board_to_dict, broadcast_lobby_reload, broadcast_game_reload
)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    # user registration endpoint
    from django.contrib.auth.forms import UserCreationForm
    
    data = dict(request.data) if hasattr(request.data, 'get') else request.data
    
    form = UserCreationForm(data)
    if form.is_valid():
        user = form.save()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            broadcast_lobby_reload()
            return Response({
                'success': True,
                'user': UserSerializer(user).data,
                'message': f'Welcome {username}!'
            }, status=status.HTTP_201_CREATED)
    
    return Response({
        'success': False,
        'errors': form.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    # user login endpoint
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'success': False,
            'error': 'Username and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        broadcast_lobby_reload()
        return Response({
            'success': True,
            'user': UserSerializer(user).data,
            'message': f'Welcome back {user.username}!'
        })
    
    return Response({
        'success': False,
        'error': 'Invalid credentials'
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout(request):
    # user logout endpoint
    username = request.user.username
    logout(request)
    broadcast_lobby_reload()
    return Response({
        'success': True,
        'message': f'Goodbye {username}!'
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_current_user(request):
    # get current authenticated user
    return Response({
        'user': UserSerializer(request.user).data
    })


class GameViewSet(viewsets.ModelViewSet):
    # viewset for game operations
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # get games for the current user
        user = self.request.user
        return Game.objects.filter(
            models.Q(white_player=user) | models.Q(black_player=user)
        ).order_by('-updated_at')
    
    def list(self, request):
        # list user's games
        games = self.get_queryset()
        serializer = self.get_serializer(games, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        # get a specific game
        game = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(game)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        # get user's active game
        active_game = get_active_game(request.user)
        if active_game:
            serializer = self.get_serializer(active_game)
            return Response(serializer.data)
        return Response({'detail': 'No active game'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def make_move(self, request, pk=None):
        # make a chess move
        game = get_object_or_404(self.get_queryset(), pk=pk)
        
        if game.status != 'active':
            return Response({
                'error': 'Game is not active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not game.is_players_turn(request.user):
            return Response({
                'error': 'Not your turn'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        from_square = request.data.get('from_square')
        to_square = request.data.get('to_square')
        
        if not from_square or not to_square:
            return Response({
                'error': 'from_square and to_square are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        board = game.get_board()
        try:
            move = chess.Move.from_uci(f"{from_square}{to_square}")
            if move in board.legal_moves:
                piece = board.piece_at(chess.parse_square(from_square))
                board.push(move)
                game.update_board(board)
                
                Move.objects.create(
                    game=game,
                    player=request.user,
                    from_square=from_square,
                    to_square=to_square,
                    piece=piece.symbol() if piece else '',
                    notation=str(move)
                )
                
                game.current_turn = 'black' if game.current_turn == 'white' else 'white'
                game.move_count += 1
                
                if board.is_checkmate():
                    game.status = 'completed'
                    game.winner = request.user
                    game.outcome = 'white_wins' if request.user == game.white_player else 'black_wins'
                elif board.is_stalemate() or board.is_insufficient_material():
                    game.status = 'completed'
                    game.outcome = 'draw'
                
                game.save()
                broadcast_game_reload(game.id)
                if game.status != 'active':
                    broadcast_lobby_reload()
                
                serializer = self.get_serializer(game)
                return Response({
                    'success': True,
                    'game': serializer.data,
                    'message': f'Move made: {from_square} to {to_square}'
                })
            else:
                return Response({
                    'error': 'Invalid move'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'Invalid move: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def resign(self, request, pk=None):
        # resign from current game
        game = get_object_or_404(self.get_queryset(), pk=pk)
        
        if game.status != 'active':
            return Response({
                'error': 'Game is not active'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user == game.white_player:
            game.winner = game.black_player
            game.outcome = 'white_resigned'
        else:
            game.winner = game.white_player
            game.outcome = 'black_resigned'
        
        game.status = 'resigned'
        game.save()
        broadcast_game_reload(game.id)
        broadcast_lobby_reload()
        
        opponent = game.get_opponent(request.user)
        serializer = self.get_serializer(game)
        return Response({
            'success': True,
            'game': serializer.data,
            'message': f'You resigned. {opponent.username} wins!'
        })
    
    @action(detail=True, methods=['get'])
    def board_state(self, request, pk=None):
        # get board state for the current user
        game = get_object_or_404(self.get_queryset(), pk=pk)
        board = game.get_board()
        board_dict = board_to_dict(board, request.user, game)
        
        is_my_turn = game.is_players_turn(request.user)
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
        
        data = {
            'board_dict': board_dict,
            'current_turn': game.current_turn,
            'is_my_turn': is_my_turn,
            'is_game_over': is_game_over,
            'result': result
        }
        
        serializer = BoardStateSerializer(data)
        return Response(serializer.data)


class GameChallengeViewSet(viewsets.ModelViewSet):
    # viewset for game challenges
    serializer_class = GameChallengeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # get challenges for the current user
        user = self.request.user
        return GameChallenge.objects.filter(
            models.Q(challenger=user) | models.Q(challenged=user)
        ).order_by('-created_at')
    
    def list(self, request):
        # list user's challenges
        challenges = self.get_queryset()
        serializer = self.get_serializer(challenges, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        # get pending challenges for the current user
        pending_challenges = GameChallenge.objects.filter(
            challenged=request.user,
            status='pending'
        )
        serializer = self.get_serializer(pending_challenges, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        # create a new challenge
        challenged_id = request.data.get('challenged_id')
        if not challenged_id:
            return Response({
                'error': 'challenged_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        challenged_user = get_object_or_404(User, id=challenged_id)
        
        if challenged_user == request.user:
            return Response({
                'error': 'You cannot challenge yourself'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if get_active_game(request.user):
            return Response({
                'error': 'You already have an active game'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if get_active_game(challenged_user):
            return Response({
                'error': f'{challenged_user.username} is already in a game'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        existing_challenge = GameChallenge.objects.filter(
            challenger=request.user,
            challenged=challenged_user,
            status='pending'
        ).first()
        
        if existing_challenge:
            serializer = self.get_serializer(existing_challenge)
            return Response({
                'success': False,
                'challenge': serializer.data,
                'message': f'You have already challenged {challenged_user.username}'
            })
        
        challenge = GameChallenge.objects.create(
            challenger=request.user,
            challenged=challenged_user
        )
        broadcast_lobby_reload()
        serializer = self.get_serializer(challenge)
        return Response({
            'success': True,
            'challenge': serializer.data,
            'message': f'Challenge sent to {challenged_user.username}!'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        # accept a game challenge
        challenge = get_object_or_404(
            GameChallenge,
            id=pk,
            challenged=request.user,
            status='pending'
        )
        
        if get_active_game(request.user):
            return Response({
                'error': 'You already have an active game'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        game = Game.objects.create(
            white_player=challenge.challenger,
            black_player=challenge.challenged
        )
        
        challenge.status = 'accepted'
        challenge.save()
        
        broadcast_lobby_reload()
        broadcast_game_reload(game.id)
        
        game_serializer = GameSerializer(game)
        return Response({
            'success': True,
            'game': game_serializer.data,
            'message': f'Challenge accepted! Game started with {challenge.challenger.username}.'
        })
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        # decline a game challenge
        challenge = get_object_or_404(
            GameChallenge,
            id=pk,
            challenged=request.user,
            status='pending'
        )
        
        challenge.status = 'declined'
        challenge.save()
        
        broadcast_lobby_reload()
        serializer = self.get_serializer(challenge)
        return Response({
            'success': True,
            'challenge': serializer.data,
            'message': f'Challenge from {challenge.challenger.username} declined.'
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_available_players(request):
    # get list of available players
    class MockRequest:
        def __init__(self, user):
            self.user = user
    
    mock_request = MockRequest(request.user)
    available_players = get_logged_in_users_excluding_current(mock_request)
    available_players = [user for user in available_players if not get_active_game(user)]
    
    serializer = UserSerializer(available_players, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_game_history(request):
    # get game history
    try:
        if request.user.is_authenticated:
            games = Game.objects.filter(
                Q(white_player=request.user) | Q(black_player=request.user)
            ).filter(status__in=['completed', 'resigned']).order_by('-updated_at')
        else:
            games = Game.objects.filter(
                status__in=['completed', 'resigned']
            ).order_by('-updated_at')[:20]
        
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response({
            'error': str(e),
            'detail': 'Error loading game history'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


from django.views.decorators.csrf import csrf_exempt

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
@csrf_exempt
def api_solo_play(request):
    # guest single player mode starts a new game every time
    if request.method == 'GET':
        request.session.pop('solo_board', None)
        request.session.pop('solo_turn', None)
        
        board_fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        solo_turn = 'white'
        request.session['solo_board'] = board_fen
        request.session['solo_turn'] = solo_turn
        
        board = chess.Board(board_fen)
        board_dict = {}
        
        piece_symbols = {
            'K': '&#9812;', 'Q': '&#9813;', 'R': '&#9814;', 'B': '&#9815;', 'N': '&#9816;', 'P': '&#9817;',
            'k': '&#9818;', 'q': '&#9819;', 'r': '&#9820;', 'b': '&#9821;', 'n': '&#9822;', 'p': '&#9823;'
        }
        
        for row in range(8):
            for col in range(8):
                square = chess.square(col, 7 - row)
                piece = board.piece_at(square)
                
                file_letter = chr(ord('a') + col)
                rank_number = str(8 - row)
                square_name = f"{file_letter}{rank_number}"
                
                if piece:
                    board_dict[square_name] = piece_symbols.get(piece.symbol(), '')
                else:
                    board_dict[square_name] = '&nbsp;'
        
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
        
        data = {
            'board_dict': board_dict,
            'current_turn': solo_turn,
            'is_my_turn': True,
            'is_game_over': is_game_over,
            'result': result
        }
        
        serializer = BoardStateSerializer(data)
        return Response(serializer.data)
    
    elif request.method == 'POST':
        if request.data.get('reset'):
            request.session['solo_board'] = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
            request.session['solo_turn'] = 'white'
            return Response({
                'success': True,
                'message': 'Board reset!'
            })
        
        from_square = request.data.get('from_square')
        to_square = request.data.get('to_square')
        
        if not from_square or not to_square:
            return Response({
                'error': 'from_square and to_square are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        board_fen = request.session.get('solo_board', 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
        
        try:
            board = chess.Board(board_fen)
            move = chess.Move.from_uci(f"{from_square}{to_square}")
            
            if move in board.legal_moves:
                board.push(move)
                request.session['solo_board'] = board.fen()
                request.session['solo_turn'] = 'black' if request.session.get('solo_turn', 'white') == 'white' else 'white'
                
                board_dict = {}
                piece_symbols = {
                    'K': '&#9812;', 'Q': '&#9813;', 'R': '&#9814;', 'B': '&#9815;', 'N': '&#9816;', 'P': '&#9817;',
                    'k': '&#9818;', 'q': '&#9819;', 'r': '&#9820;', 'b': '&#9821;', 'n': '&#9822;', 'p': '&#9823;'
                }
                
                for row in range(8):
                    for col in range(8):
                        square = chess.square(col, 7 - row)
                        piece = board.piece_at(square)
                        
                        file_letter = chr(ord('a') + col)
                        rank_number = str(8 - row)
                        square_name = f"{file_letter}{rank_number}"
                        
                        if piece:
                            board_dict[square_name] = piece_symbols.get(piece.symbol(), '')
                        else:
                            board_dict[square_name] = '&nbsp;'
                
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
                
                data = {
                    'board_dict': board_dict,
                    'current_turn': request.session.get('solo_turn', 'white'),
                    'is_my_turn': True,
                    'is_game_over': is_game_over,
                    'result': result
                }
                
                serializer = BoardStateSerializer(data)
                return Response({
                    'success': True,
                    'board_state': serializer.data,
                    'message': f'Move: {from_square} to {to_square}'
                })
            else:
                return Response({
                    'error': 'Invalid move!'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'Invalid move: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

