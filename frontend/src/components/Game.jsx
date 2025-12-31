import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'
import websocket from '../services/websocket'
import ChessBoard from './ChessBoard'

function Game() {
  const { gameId } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const [game, setGame] = useState(null)
  const [boardState, setBoardState] = useState(null)
  const [fromSquare, setFromSquare] = useState('')
  const [toSquare, setToSquare] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    let mounted = true
    let pollInterval = null
    let lastMoveCount = null
    let lastStatus = null
    let resignationHandled = false // Flag to prevent multiple resignation popups

    const loadGameData = async () => {
      if (!mounted) return
      const gameData = await loadGame()
      // Initialize polling state from initial load
      if (gameData && mounted) {
        lastMoveCount = gameData.move_count
        lastStatus = gameData.status
        console.log('Polling initialized from loadGame:', { lastMoveCount, lastStatus })
      }
    }

    loadGameData()

    // Connect to game WebSocket
    const handleWebSocketMessage = async (data) => {
      if (!mounted || resignationHandled) return // Don't process if resignation already handled
      console.log('Game WebSocket message received:', data)
      
      if (data.action === 'game_refresh') {
        if (data.data) {
          console.log('Updating game state from WebSocket', data.data)
          // Check if opponent resigned (only show popup to the winner, not the one who resigned)
          if (data.data.game && data.data.game.status === 'resigned' && !resignationHandled) {
            const currentStatus = game?.status || 'active'
            // Check if current user is NOT the one who resigned (i.e., they are the winner)
            if (currentStatus === 'active' && data.data.game.status === 'resigned' && mounted && user 
                && data.data.game.winner) {
              const winnerId = typeof data.data.game.winner === 'object' ? data.data.game.winner.id : data.data.game.winner
              if (winnerId === user.id) {
                // Mark resignation as handled FIRST to prevent any other code from running
                resignationHandled = true
                // Stop polling IMMEDIATELY to prevent further checks
                if (pollInterval) {
                  clearInterval(pollInterval)
                  pollInterval = null
                }
                websocket.disconnectGame(gameId)
                
                // Current user is the winner - opponent resigned
                const isWhitePlayer = data.data.game.white_player.id === user.id
                const opponent = isWhitePlayer 
                  ? data.data.game.black_player 
                  : data.data.game.white_player
                const opponentName = typeof opponent === 'object' ? opponent.username : 'Opponent'
                
                alert(`${opponentName} has resigned. You win!`)
                
                if (mounted) {
                  navigate('/')
                }
                return
              }
            }
          }
          
          // Update game and board state from WebSocket data
          if (data.data.game) {
            setGame(data.data.game)
          }
          if (data.data.board_state) {
            console.log('Setting board state from WebSocket data')
            setBoardState(data.data.board_state)
          } else {
            console.log('Board state not in WebSocket, reloading from API...')
            try {
              const boardResponse = await api.get(`/games/${gameId}/board_state/`)
              if (mounted) {
                setBoardState(boardResponse.data)
              }
            } catch (error) {
              console.error('Failed to reload board state:', error)
            }
          }
          setError('')
        } else {
          console.log('No data in WebSocket message, reloading game...')
          if (mounted) {
            loadGame()
          }
        }
      } else if (data.action === 'reload') {
        console.log('Received reload command, reloading game...')
        if (mounted) {
          loadGame()
        }
      }
    }
    
    const connectTimeout = setTimeout(() => {
      websocket.connectGame(gameId, handleWebSocketMessage)
    }, 100)

    setTimeout(async () => {
      try {
        const gameResponse = await api.get(`/games/${gameId}/`)
        if (mounted && gameResponse.data) {
          lastMoveCount = gameResponse.data.move_count
          lastStatus = gameResponse.data.status
        }
      } catch (error) {
        console.error('Error initializing polling state:', error)
      }
    }, 1000)
    
    pollInterval = setInterval(async () => {
      if (!mounted || resignationHandled) return
      try {
        const gameResponse = await api.get(`/games/${gameId}/`)
        const currentGame = gameResponse.data
        
        const moveCountChanged = lastMoveCount !== null && lastMoveCount !== currentGame.move_count
        const statusChanged = lastStatus !== null && lastStatus !== currentGame.status
        
        if (moveCountChanged || statusChanged) {
          console.log('Game state changed (polling), reloading...', {
            oldMoveCount: lastMoveCount,
            newMoveCount: currentGame.move_count,
            oldStatus: lastStatus,
            newStatus: currentGame.status
          })
          
          if (statusChanged && currentGame.status === 'resigned' && lastStatus === 'active' && !resignationHandled) {
            if (mounted && user && currentGame.winner) {
              const winnerId = typeof currentGame.winner === 'object' ? currentGame.winner.id : currentGame.winner
              if (winnerId === user.id) {
                resignationHandled = true
                if (pollInterval) {
                  clearInterval(pollInterval)
                  pollInterval = null
                }
                websocket.disconnectGame(gameId)
                
                const isWhitePlayer = currentGame.white_player.id === user.id
                const opponent = isWhitePlayer 
                  ? currentGame.black_player 
                  : currentGame.white_player
                const opponentName = typeof opponent === 'object' ? opponent.username : 'Opponent'
                
                alert(`${opponentName} has resigned. You win!`)
                
                if (mounted) {
                  navigate('/')
                }
                return
              }
            }
          }
          
          const boardResponse = await api.get(`/games/${gameId}/board_state/`)
          if (mounted) {
            setGame(currentGame)
            setBoardState(boardResponse.data)
            lastMoveCount = currentGame.move_count
            lastStatus = currentGame.status
          }
        }
      } catch (error) {
        console.error('Polling error:', error)
      }
    }, 2000) // Poll every 2 seconds

    return () => {
      mounted = false
      clearTimeout(connectTimeout)
      if (pollInterval) {
        clearInterval(pollInterval)
      }
      websocket.disconnectGame(gameId)
    }
  }, [gameId])

  const loadGame = async () => {
    try {
      setLoading(true)
      const gameResponse = await api.get(`/games/${gameId}/`)
      setGame(gameResponse.data)

      const boardResponse = await api.get(`/games/${gameId}/board_state/`)
      setBoardState(boardResponse.data)
      
      return gameResponse.data
    } catch (error) {
      setError('Failed to load game')
      console.error(error)
      return null
    } finally {
      setLoading(false)
    }
  }

  const validateSquare = (square) => {
    const trimmed = square.toLowerCase().trim()
    if (trimmed.length !== 2) return false
    const file = trimmed[0]
    const rank = trimmed[1]
    return file >= 'a' && file <= 'h' && rank >= '1' && rank <= '8'
  }

  const handleMoveSubmit = async (e) => {
    e.preventDefault()
    if (!fromSquare || !toSquare) {
      setError('Please enter both from and to squares')
      return
    }
    
    const from = fromSquare.toLowerCase().trim()
    const to = toSquare.toLowerCase().trim()
    
    if (!validateSquare(from)) {
      setError(`Invalid from square: ${fromSquare}. Use format like "e2"`)
      return
    }
    
    if (!validateSquare(to)) {
      setError(`Invalid to square: ${toSquare}. Use format like "e4"`)
      return
    }
    
    await makeMove(from, to)
    setFromSquare('')
    setToSquare('')
  }

  const makeMove = async (from, to) => {
    try {
      setMessage('')
      setError('')
      const response = await api.post(`/games/${gameId}/make_move/`, {
        from_square: from,
        to_square: to
      })

      if (response.data.success) {
        setGame(response.data.game)
        setMessage(response.data.message)
        const boardResponse = await api.get(`/games/${gameId}/board_state/`)
        setBoardState(boardResponse.data)
        console.log('Move successful, WebSocket should notify opponent')
      } else {
        const errorMsg = response.data.error || response.data.detail || 'Failed to make move'
        setError(errorMsg)
        console.error('Move error:', response.data)
      }
    } catch (error) {
      const errorMsg = error.response?.data?.error || 
                      error.response?.data?.detail || 
                      error.message || 
                      'Failed to make move'
      setError(errorMsg)
      console.error('Move exception:', error.response?.data || error)
    }
  }

  const handleResign = async () => {
    if (!window.confirm('Are you sure you want to resign? This will end the game and your opponent will win.')) {
      return
    }

    try {
      const response = await api.post(`/games/${gameId}/resign/`)
      if (response.data.success) {
        navigate('/')
      }
    } catch (error) {
      setError(error.response?.data?.error || 'Failed to resign')
    }
  }

  if (loading) {
    return (
      <div className="container mt-5">
        <div className="text-center">
          <div className="spinner-border" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </div>
      </div>
    )
  }

  if (error && !game) {
    return (
      <div className="container mt-5">
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
        <button className="btn btn-primary" onClick={() => navigate('/')}>
          Back to Lobby
        </button>
      </div>
    )
  }

  if (!game || !boardState || !user) {
    return null
  }

  const opponent = game.white_player.id === user.id
    ? game.black_player
    : game.white_player

  return (
    <div className="container mt-5">
      <h1 className="mb-4">Chess Game</h1>
      
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}
      
      {message && (
        <div className="alert alert-success" role="alert">
          {message}
        </div>
      )}

      <div className="game-info">
        <div className="row">
          <div className="col-md-6">
            <h5>White: {game.white_player.username}</h5>
            <h5>Black: {game.black_player.username}</h5>
          </div>
          <div className="col-md-6">
            <h5>Status: {game.status}</h5>
            <h5>Current Turn: {game.current_turn}</h5>
            {boardState.is_game_over && boardState.result && (
              <div className="alert alert-info mt-3">
                <strong>{boardState.result}</strong>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="text-center">
        <ChessBoard
          boardDict={boardState.board_dict}
        />
      </div>

      <div className="text-center mt-4">
        {boardState.is_my_turn && !boardState.is_game_over && (
          <div className="card mx-auto" style={{ maxWidth: '500px' }}>
            <div className="card-body">
              <h5 className="card-title">Make a Move</h5>
              <form onSubmit={handleMoveSubmit}>
                <div className="row mb-3">
                  <div className="col-md-6">
                    <label htmlFor="fromSquare" className="form-label">From Square</label>
                    <input
                      type="text"
                      className="form-control"
                      id="fromSquare"
                      placeholder="e.g., e2"
                      value={fromSquare}
                      onChange={(e) => setFromSquare(e.target.value)}
                      maxLength="2"
                      required
                    />
                  </div>
                  <div className="col-md-6">
                    <label htmlFor="toSquare" className="form-label">To Square</label>
                    <input
                      type="text"
                      className="form-control"
                      id="toSquare"
                      placeholder="e.g., e4"
                      value={toSquare}
                      onChange={(e) => setToSquare(e.target.value)}
                      maxLength="2"
                      required
                    />
                  </div>
                </div>
                <button type="submit" className="btn btn-primary">
                  Make Move
                </button>
              </form>
            </div>
          </div>
        )}
        {!boardState.is_my_turn && !boardState.is_game_over && (
          <div className="alert alert-warning">
            Waiting for {opponent.username} to make a move...
          </div>
        )}
        {game.status === 'active' && (
          <div className="mt-3">
            <button className="btn btn-danger" onClick={handleResign}>
              Resign
            </button>
          </div>
        )}
        {game.status !== 'active' && (
          <button className="btn btn-primary" onClick={() => navigate('/')}>
            Back to Lobby
          </button>
        )}
      </div>
    </div>
  )
}

export default Game

