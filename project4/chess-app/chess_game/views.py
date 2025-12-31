from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.db import models
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import now
from django.views.decorators.http import require_http_methods
import chess

from .models import Game, GameChallenge, Move


def home_view(request):
    """Main home view - route to login, new game, or active game"""
    if not request.user.is_authenticated:
        return redirect('chess_game:login')
    
    # Check if user has an active game
    active_game = get_active_game(request.user)
    if active_game:
        return redirect('chess_game:game')
    
    # Show new game screen
    return new_game_view(request)


def new_game_view(request):
    """New game screen with available players and game history"""
    if not request.user.is_authenticated:
        return redirect('chess_game:login')
    
    # Get available players (logged in users without active games)
    available_players = get_logged_in_users_excluding_current(request)
    available_players = [user for user in available_players if not get_active_game(user)]
    
    # Get user's game history
    user_games = Game.objects.filter(
        models.Q(white_player=request.user) | models.Q(black_player=request.user),
        status__in=['completed', 'resigned']  # project-3
    ).order_by('-updated_at')[:10]
    
    # Get pending challenges
    pending_challenges = GameChallenge.objects.filter(
        challenged=request.user,
        status='pending'
    )
    
    context = {
        'available_players': available_players,
        'user_games': user_games,
        'pending_challenges': pending_challenges,
    }
    return render(request, 'chess_game/new_game.html', context)


def join_view(request):
    """User registration"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            messages.success(request, f'Welcome {username}!')
            broadcast_lobby_reload()
            return redirect('chess_game:home')
    else:
        form = UserCreationForm()
    
    return render(request, 'chess_game/join.html', {'form': form})


def login_view(request):
    """User login"""
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back {user.username}!')
            broadcast_lobby_reload()
            return redirect('chess_game:home')
    else:
        form = AuthenticationForm()
    
    return render(request, 'chess_game/login.html', {'form': form})


def logout_view(request):
    """User logout"""
    messages.info(request, f'Goodbye {request.user.username}!')
    logout(request)
    broadcast_lobby_reload()
    return redirect('chess_game:login')


def history_view(request):
    """Game history page (accessible to guests)"""
    if request.user.is_authenticated:
        games = Game.objects.filter(
            models.Q(white_player=request.user) | models.Q(black_player=request.user)
        ).filter(status__in=['completed', 'resigned']).order_by('-updated_at')  # project-3
    else:
        games = Game.objects.filter(status__in=['completed', 'resigned']).order_by('-updated_at')[:20]  # project-3
    
    return render(request, 'chess_game/history.html', {'games': games})


def rules_view(request):
    """Chess rules page (accessible to guests)"""
    return render(request, 'chess_game/rules.html')


def about_view(request):
    """About page (accessible to guests)"""
    return render(request, 'chess_game/about.html')


def play_solo_view(request):
    """Guest single-player mode (accessible to all)"""
    # Initialize board state from session or create new
    if 'solo_board' not in request.session:
        request.session['solo_board'] = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
        request.session['solo_turn'] = 'white'
    
    # Handle move submission
    if request.method == 'POST':
        from_square = request.POST.get('from_square')
        to_square = request.POST.get('to_square')
        
        if from_square and to_square:
            try:
                board = chess.Board(request.session['solo_board'])
                move = chess.Move.from_uci(f"{from_square}{to_square}")
                
                if move in board.legal_moves:
                    board.push(move)
                    request.session['solo_board'] = board.fen()
                    request.session['solo_turn'] = 'black' if request.session['solo_turn'] == 'white' else 'white'
                    messages.success(request, f'Move: {from_square} to {to_square}')
                else:
                    messages.error(request, 'Invalid move!')
            except Exception as e:
                messages.error(request, f'Invalid move: {str(e)}')
        
        # Reset board action
        if request.POST.get('reset'):
            request.session['solo_board'] = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
            request.session['solo_turn'] = 'white'
            messages.info(request, 'Board reset!')
        
        return redirect('chess_game:play_solo')
    
    # Get current board state
    board = chess.Board(request.session['solo_board'])
    board_dict = {}
    
    # Chess piece Unicode symbols
    piece_symbols = {
        'K': '&#9812;', 'Q': '&#9813;', 'R': '&#9814;', 'B': '&#9815;', 'N': '&#9816;', 'P': '&#9817;',
        'k': '&#9818;', 'q': '&#9819;', 'r': '&#9820;', 'b': '&#9821;', 'n': '&#9822;', 'p': '&#9823;'
    }
    
    # Convert board to dictionary
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
    
    context = {
        'board_dict': board_dict,
        'current_turn': request.session['solo_turn'],
        'is_game_over': board.is_game_over(),
        'result': None
    }
    
    if board.is_game_over():
        if board.is_checkmate():
            winner = 'Black' if board.turn else 'White'
            context['result'] = f'{winner} wins by checkmate!'
        elif board.is_stalemate():
            context['result'] = 'Draw by stalemate!'
        elif board.is_insufficient_material():
            context['result'] = 'Draw by insufficient material!'
    
    return render(request, 'chess_game/play_solo.html', context)


@login_required
def game_view(request):
    """Active game view with chessboard"""
    active_game = get_active_game(request.user)
    if not active_game:
        messages.error(request, 'No active game found.')
        return redirect('chess_game:home')
    
    # Convert board to template-friendly format
    board_dict = board_to_dict(active_game.get_board(), request.user, active_game)
    
    # Check if it's the user's turn
    is_my_turn = active_game.is_players_turn(request.user)
    
    context = {
        'game': active_game,
        'board_dict': board_dict,
        'is_my_turn': is_my_turn,
        'opponent': active_game.get_opponent(request.user),
    }
    return render(request, 'chess_game/game.html', context)


@login_required
def challenge_user(request, user_id):
    """Challenge another user to a game"""
    challenged_user = get_object_or_404(User, id=user_id)
    
    if challenged_user == request.user:
        messages.error(request, 'You cannot challenge yourself.')
        return redirect('chess_game:home')
    
    if get_active_game(request.user):
        messages.error(request, 'You already have an active game.')
        return redirect('chess_game:home')
    
    if get_active_game(challenged_user):
        messages.error(request, f'{challenged_user.username} is already in a game.')
        return redirect('chess_game:home')
    
    # Check if there's already a pending challenge
    existing_challenge = GameChallenge.objects.filter(
        challenger=request.user,
        challenged=challenged_user,
        status='pending'
    ).first()
    
    if existing_challenge:
        messages.info(request, f'You have already challenged {challenged_user.username}.')
    else:
        GameChallenge.objects.create(
            challenger=request.user,
            challenged=challenged_user
        )
        messages.success(request, f'Challenge sent to {challenged_user.username}!')
    
    broadcast_lobby_reload()
    return redirect('chess_game:home')


@login_required
def accept_challenge(request, challenge_id):
    """Accept a game challenge"""
    challenge = get_object_or_404(GameChallenge, id=challenge_id, challenged=request.user, status='pending')
    
    if get_active_game(request.user):
        messages.error(request, 'You already have an active game.')
        return redirect('chess_game:home')
    
    # Create new game
    game = Game.objects.create(
        white_player=challenge.challenger,
        black_player=challenge.challenged
    )
    
    # Update challenge status
    challenge.status = 'accepted'
    challenge.save()
    
    messages.success(request, f'Challenge accepted! Game started with {challenge.challenger.username}.')
    broadcast_lobby_reload()
    broadcast_game_reload(game.id)
    return redirect('chess_game:game')


@login_required
def decline_challenge(request, challenge_id):
    """Decline a game challenge"""
    challenge = get_object_or_404(GameChallenge, id=challenge_id, challenged=request.user, status='pending')
    
    challenge.status = 'declined'
    challenge.save()
    
    messages.info(request, f'Challenge from {challenge.challenger.username} declined.')
    broadcast_lobby_reload()
    return redirect('chess_game:home')


@login_required
@require_http_methods(["POST"])
def make_move(request):
    """Make a chess move"""
    active_game = get_active_game(request.user)
    if not active_game:
        messages.error(request, 'No active game found.')
        return redirect('chess_game:home')
    
    if not active_game.is_players_turn(request.user):
        messages.error(request, 'Not your turn.')
        return redirect('chess_game:game')
    
    from_square = request.POST.get('from_square')
    to_square = request.POST.get('to_square')
    
    if not from_square or not to_square:
        messages.error(request, 'Invalid move data.')
        return redirect('chess_game:game')
    
    # Validate move using python-chess
    board = active_game.get_board()
    try:
        move = chess.Move.from_uci(f"{from_square}{to_square}")
        if move in board.legal_moves:
            # Execute move
            piece = board.piece_at(chess.parse_square(from_square))
            board.push(move)
            active_game.update_board(board)
            
            # Record move
            Move.objects.create(
                game=active_game,
                player=request.user,
                from_square=from_square,
                to_square=to_square,
                piece=piece.symbol() if piece else '',
                notation=str(move)
            )
            
            # Update game state
            active_game.current_turn = 'black' if active_game.current_turn == 'white' else 'white'
            active_game.move_count += 1
            
            # Check for game end conditions
            if board.is_checkmate():
                active_game.status = 'completed'
                active_game.winner = request.user
                active_game.outcome = 'white_wins' if request.user == active_game.white_player else 'black_wins'
            elif board.is_stalemate() or board.is_insufficient_material():
                active_game.status = 'completed'
                active_game.outcome = 'draw'
            
            active_game.save()
            broadcast_game_reload(active_game.id)
            if active_game.status != 'active':
                broadcast_lobby_reload()
            
            messages.success(request, f'Move made: {from_square} to {to_square}')
            return redirect('chess_game:game')
        else:
            messages.error(request, 'Invalid move.')
            return redirect('chess_game:game')
    except Exception as e:
        messages.error(request, f'Invalid move: {str(e)}')
        return redirect('chess_game:game')


@login_required
def resign_game(request):
    """Resign from current game"""
    active_game = get_active_game(request.user)
    if not active_game:
        messages.error(request, 'No active game found.')
        return redirect('chess_game:home')
    
    # Determine winner and outcome
    if request.user == active_game.white_player:
        active_game.winner = active_game.black_player
        active_game.outcome = 'white_resigned'
    else:
        active_game.winner = active_game.white_player
        active_game.outcome = 'black_resigned'
    
    active_game.status = 'resigned'
    active_game.save()
    broadcast_game_reload(active_game.id)
    broadcast_lobby_reload()
    
    opponent = active_game.get_opponent(request.user)
    messages.info(request, f'You resigned. {opponent.username} wins!')
    return redirect('chess_game:home')


# Helper Functions
def get_logged_in_users_excluding_current(request):
    """Get all logged-in users excluding the current user"""
    active_sessions = Session.objects.filter(expire_date__gte=now())
    user_ids = []
    
    for session in active_sessions:
        session_data = session.get_decoded()
        user_id = session_data.get('_auth_user_id')
        if user_id:
            user_ids.append(user_id)
    
    # Convert IDs to unique set and exclude the current user
    logged_in_users = User.objects.filter(id__in=set(user_ids)).exclude(id=request.user.id)
    return logged_in_users


def get_active_game(user):
    """Get user's current active game if exists"""
    return Game.objects.filter(
        models.Q(white_player=user) | models.Q(black_player=user),
        status='active'
    ).first()


def board_to_dict(chess_board, user, game):
    """Convert python-chess board to template-friendly dictionary"""
    board_dict = {}
    
    # Chess piece Unicode symbols
    piece_symbols = {
        'K': '&#9812;', 'Q': '&#9813;', 'R': '&#9814;', 'B': '&#9815;', 'N': '&#9816;', 'P': '&#9817;',
        'k': '&#9818;', 'q': '&#9819;', 'r': '&#9820;', 'b': '&#9821;', 'n': '&#9822;', 'p': '&#9823;'
    }
    
    # Determine perspective (flip board for black player)
    is_black_player = user == game.black_player
    
    for row in range(8):
        for col in range(8):
            square = chess.square(col, 7 - row) if not is_black_player else chess.square(7 - col, row)
            piece = chess_board.piece_at(square)
            
            # Adjust coordinates based on player perspective
            if is_black_player:
                # For black player, flip both file and rank
                file_letter = chr(ord('h') - col)  # h,g,f,e,d,c,b,a
                rank_number = str(row + 1)        # 1,2,3,4,5,6,7,8
            else:
                # For white player, standard coordinates
                file_letter = chr(ord('a') + col)  # a,b,c,d,e,f,g,h
                rank_number = str(8 - row)         # 8,7,6,5,4,3,2,1
            
            square_name = f"{file_letter}{rank_number}"
            
            if piece:
                board_dict[square_name] = piece_symbols.get(piece.symbol(), '')
            else:
                board_dict[square_name] = '&nbsp;'
    
    return board_dict


def broadcast_lobby_reload():
    """Notify lobby websocket clients to refresh."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        'lobby',
        {'type': 'lobby.refresh'},  # project-3
    )


def broadcast_game_reload(game_id):
    """Notify game websocket clients to refresh."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        f'game_{game_id}',
        {'type': 'game.refresh'},  # project-3
    )