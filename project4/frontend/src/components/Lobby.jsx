import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import websocket from '../services/websocket'

function Lobby() {
  const [availablePlayers, setAvailablePlayers] = useState([])
  const [pendingChallenges, setPendingChallenges] = useState([])
  const [gameHistory, setGameHistory] = useState([])
  const [activeGame, setActiveGame] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    let mounted = true

    const loadData = async () => {
      if (!mounted) return
      await loadLobbyData()
      await checkActiveGame()
    }

    loadData()

    const handleWebSocketMessage = (data) => {
      if (!mounted) return
      if (data.action === 'lobby_refresh') {
        if (data.data) {
          setAvailablePlayers(data.data.available_players || [])
          setPendingChallenges(data.data.pending_challenges || [])
          api.get('/games/history/').then(response => {
            if (mounted) {
              const historyData = response.data || []
              console.log('WebSocket: Game history loaded:', historyData.length, 'games')
              const filteredHistory = historyData.filter(game => 
                game.status === 'completed' || game.status === 'resigned'
              )
              console.log('WebSocket: Filtered game history:', filteredHistory.length, 'games')
              setGameHistory(filteredHistory)
            }
          }).catch((error) => {
            console.error('WebSocket: Error loading game history:', error)
            if (mounted) {
              const historyData = data.data.game_history || []
              const filteredHistory = historyData.filter(game => 
                game.status === 'completed' || game.status === 'resigned'
              )
              setGameHistory(filteredHistory)
            }
          })
          const currentPath = window.location.pathname
          if (currentPath === '/' || currentPath === '/lobby') {
            checkActiveGame()
          }
        } else {
          loadLobbyData()
          checkActiveGame()
        }
      }
    }
    
    websocket.connectLobby(handleWebSocketMessage)

    const pollInterval = setInterval(async () => {
      if (!mounted) return
      try {
        const currentPath = window.location.pathname
        if (currentPath === '/' || currentPath === '/lobby') {
          await checkActiveGame()
        }
        
        try {
          const challengesResponse = await api.get('/challenges/pending/')
          setPendingChallenges(challengesResponse.data || [])
        } catch (error) {
        }
        
        try {
          const historyResponse = await api.get('/games/history/')
          const historyData = historyResponse.data || []
          const filteredHistory = historyData.filter(game => 
            game.status === 'completed' || game.status === 'resigned'
          )
          setGameHistory(filteredHistory)
        } catch (error) {
        }
      } catch (error) {
      }
    }, 2000)

    return () => {
      mounted = false
      clearInterval(pollInterval)
      websocket.disconnectLobby()
    }
  }, [])

  const loadLobbyData = async () => {
    try {
      setLoading(true)
      setError('')
      
      try {
        const playersResponse = await api.get('/players/available/')
        setAvailablePlayers(playersResponse.data || [])
      } catch (error) {
        console.error('Error loading available players:', error)
        setAvailablePlayers([])
      }

      // Load pending challenges
      try {
        const challengesResponse = await api.get('/challenges/pending/')
        setPendingChallenges(challengesResponse.data || [])
      } catch (error) {
        console.error('Error loading pending challenges:', error)
        setPendingChallenges([])
      }

      try {
        const historyResponse = await api.get('/games/history/')
        const historyData = historyResponse.data || []
        console.log('Game history API response:', historyData.length, 'games')
        console.log('Raw game history data:', historyData)
        
        const statusCounts = historyData.reduce((acc, game) => {
          acc[game.status] = (acc[game.status] || 0) + 1
          return acc
        }, {})
        console.log('Game history by status:', statusCounts)
        
        const resignedGames = historyData.filter(game => game.status === 'resigned')
        console.log('Resigned games found:', resignedGames.length, resignedGames)
        
        const filteredHistory = historyData.filter(game => 
          game.status === 'completed' || game.status === 'resigned'
        )
        console.log('Filtered game history:', filteredHistory.length, 'games (completed/resigned)')
        console.log('Setting game history state with:', filteredHistory.length, 'games')
        setGameHistory(filteredHistory)
      } catch (error) {
        console.error('Error loading game history:', error)
        console.error('Error details:', error.response?.data)
        setGameHistory([])
      }
    } catch (error) {
      console.error('Unexpected error loading lobby data:', error)
      setError('Failed to load some lobby data. Please refresh the page.')
    } finally {
      setLoading(false)
    }
  }

  const checkActiveGame = async () => {
    try {
      const response = await api.get('/games/active/') // This should be /games/active/ via ViewSet action
      const currentPath = window.location.pathname
      
      if (response.data && response.data.id) {
        if (currentPath === '/' || currentPath === '/lobby') {
          if (!activeGame || activeGame.id !== response.data.id) {
            setActiveGame(response.data)
            navigate(`/game/${response.data.id}`)
          }
        }
      } else {
        if (activeGame) {
          setActiveGame(null)
        }
      }
    } catch (error) {
      if (error.response?.status === 404) {
        if (activeGame) {
          setActiveGame(null)
        }
      } else {
        console.error('Error checking active game:', error)
      }
    }
  }

  const handleChallenge = async (playerId) => {
    try {
      const response = await api.post('/challenges/', { challenged_id: playerId })
      if (response.data.success) {
        loadLobbyData()
      } else {
        alert(response.data.message || 'Failed to send challenge')
      }
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to send challenge')
    }
  }

  const handleAcceptChallenge = async (challengeId) => {
    try {
      const response = await api.post(`/challenges/${challengeId}/accept/`)
      if (response.data.success) {
        navigate(`/game/${response.data.game.id}`)
      }
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to accept challenge')
    }
  }

  const handleDeclineChallenge = async (challengeId) => {
    try {
      await api.post(`/challenges/${challengeId}/decline/`)
      loadLobbyData()
    } catch (error) {
      alert(error.response?.data?.error || 'Failed to decline challenge')
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

  return (
    <div className="container mt-5">
      <h1 className="mb-4">Chess Lobby</h1>
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      <div className="row">
        {/* Available Players */}
        <div className="col-md-4 mb-4">
          <div className="card">
            <div className="card-header">
              <h5>Available Players</h5>
            </div>
            <div className="card-body">
              {availablePlayers.length === 0 ? (
                <p className="text-muted">No available players</p>
              ) : (
                <ul className="list-group">
                  {availablePlayers.map((player) => (
                    <li key={player.id} className="list-group-item d-flex justify-content-between align-items-center">
                      <span>{player.username}</span>
                      <button
                        className="btn btn-sm btn-primary"
                        onClick={() => handleChallenge(player.id)}
                      >
                        Challenge
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>

        {/* Pending Challenges */}
        <div className="col-md-4 mb-4">
          <div className="card">
            <div className="card-header">
              <h5>Pending Challenges</h5>
            </div>
            <div className="card-body">
              {pendingChallenges.length === 0 ? (
                <p className="text-muted">No pending challenges</p>
              ) : (
                <ul className="list-group">
                  {pendingChallenges.map((challenge) => (
                    <li key={challenge.id} className="list-group-item">
                      <div className="d-flex justify-content-between align-items-center">
                        <span>{challenge.challenger.username} challenged you</span>
                        <div>
                          <button
                            className="btn btn-sm btn-success me-2"
                            onClick={() => handleAcceptChallenge(challenge.id)}
                          >
                            Accept
                          </button>
                          <button
                            className="btn btn-sm btn-danger"
                            onClick={() => handleDeclineChallenge(challenge.id)}
                          >
                            Decline
                          </button>
                        </div>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>

        {/* Game History */}
        <div className="col-md-4 mb-4">
          <div className="card">
            <div className="card-header">
              <h5>Game History</h5>
            </div>
            <div className="card-body">
              {gameHistory.length === 0 ? (
                <div>
                  <p className="text-muted">No game history</p>
                  <small className="text-muted">(Total games in state: {gameHistory.length})</small>
                </div>
              ) : (
                <ul className="list-group">
                  {gameHistory.map((game) => {
                    if (game.status === 'resigned') {
                      console.log('Rendering resigned game:', game.id, game)
                    }
                    return (
                      <li key={game.id} className="list-group-item">
                        <div>
                          <strong>{game.white_player?.username || 'Unknown'}</strong> vs{' '}
                          <strong>{game.black_player?.username || 'Unknown'}</strong>
                        </div>
                        <div>
                          <small className="text-muted">
                            Status: <strong className={game.status === 'resigned' ? 'text-danger' : 'text-primary'}>
                              {game.status === 'resigned' ? 'Resigned' : game.status}
                            </strong> | Outcome: {game.outcome || 'N/A'}
                          </small>
                        </div>
                        {game.winner && (
                          <div>
                            <small className="text-success">
                              Winner: <strong>{typeof game.winner === 'object' ? game.winner.username : 'Unknown'}</strong>
                            </small>
                          </div>
                        )}
                        {game.status === 'resigned' && game.outcome && (
                          <div>
                            <small className="text-info">
                              {game.outcome === 'white_resigned' ? 'White resigned' : 'Black resigned'}
                            </small>
                          </div>
                        )}
                        <div>
                          <small className="text-muted">
                            Moves: {game.move_count} | {new Date(game.updated_at).toLocaleString()}
                          </small>
                        </div>
                      </li>
                    )
                  })}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Lobby

