import { useState, useEffect } from 'react'
import api from '../services/api'

function History() {
  const [games, setGames] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    loadHistory()
  }, [])

  const loadHistory = async () => {
    try {
      setLoading(true)
      const response = await api.get('/games/history/')
      setGames(response.data)
    } catch (error) {
      setError('Failed to load game history')
      console.error(error)
    } finally {
      setLoading(false)
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
      <h1 className="mb-4">Game History</h1>
      
      {error && (
        <div className="alert alert-danger" role="alert">
          {error}
        </div>
      )}

      {games.length === 0 ? (
        <div className="alert alert-info">
          No game history available.
        </div>
      ) : (
        <div className="table-responsive">
          <table className="table table-striped">
            <thead>
              <tr>
                <th>White Player</th>
                <th>Black Player</th>
                <th>Status</th>
                <th>Outcome</th>
                <th>Winner</th>
                <th>Moves</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              {games.map((game) => (
                <tr key={game.id}>
                  <td>{game.white_player.username}</td>
                  <td>{game.black_player.username}</td>
                  <td>{game.status}</td>
                  <td>{game.outcome || '-'}</td>
                  <td>{game.winner ? game.winner.username : '-'}</td>
                  <td>{game.move_count}</td>
                  <td>{new Date(game.updated_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default History

