import { useState, useEffect } from 'react'
import api from '../services/api'
import ChessBoard from './ChessBoard'

function SoloPlay() {
  const [boardState, setBoardState] = useState(null)
  const [fromSquare, setFromSquare] = useState('')
  const [toSquare, setToSquare] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    loadBoardState()
  }, [])

  const loadBoardState = async () => {
    try {
      setLoading(true)
      const response = await api.get('/solo/')
      setBoardState(response.data)
    } catch (error) {
      setError('Failed to load board')
      console.error(error)
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
      const response = await api.post('/solo/', {
        from_square: from,
        to_square: to
      })

      if (response.data.success) {
        setBoardState(response.data.board_state)
        setMessage(response.data.message)
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

  const handleReset = async () => {
    try {
      const response = await api.post('/solo/', { reset: true })
      if (response.data.success) {
        setMessage(response.data.message)
        loadBoardState()
      }
    } catch (error) {
      setError('Failed to reset board')
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

  if (!boardState) {
    return null
  }

  return (
    <div className="container mt-5">
      <h1 className="mb-4">Solo Play</h1>
      
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

      {boardState.is_game_over && boardState.result && (
        <div className="alert alert-info">
          <strong>{boardState.result}</strong>
        </div>
      )}

      <div className="text-center">
        <ChessBoard
          boardDict={boardState.board_dict}
        />
      </div>

      <div className="text-center mt-4">
        <p className="mb-3">
          <strong>Current Turn:</strong> {boardState.current_turn}
        </p>
        {!boardState.is_game_over && (
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
        <div className="mt-3">
          <button className="btn btn-primary me-2" onClick={handleReset}>
            Reset Board
          </button>
        </div>
      </div>
    </div>
  )
}

export default SoloPlay

