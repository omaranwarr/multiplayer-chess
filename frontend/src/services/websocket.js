class WebSocketService {
  constructor() {
    this.lobbySocket = null
    this.gameSockets = {}
    this.reconnectingLobby = false
    this.reconnectingGames = {}
  }

  connectLobby(onMessage) {
    if (this.lobbySocket) {
      if (this.lobbySocket.readyState === WebSocket.OPEN || this.lobbySocket.readyState === WebSocket.CONNECTING) {
        return
      }
      this.lobbySocket.close()
      this.lobbySocket = null
    }
    
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = window.location.host
    const wsUrl = `${wsProtocol}//${wsHost}/ws/lobby/`
    
    this.lobbySocket = new WebSocket(wsUrl)
    
    this.lobbySocket.onopen = () => {
    }
    
    this.lobbySocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }
    
    this.lobbySocket.onerror = (error) => {
      console.error('Lobby WebSocket error:', error)
    }
    
    this.lobbySocket.onclose = (event) => {
      this.lobbySocket = null
      if (event.code !== 1000 && event.code !== 1001) {
        if (!this.reconnectingLobby) {
          this.reconnectingLobby = true
          setTimeout(() => {
            this.reconnectingLobby = false
            if (!this.lobbySocket) {
              this.connectLobby(onMessage)
            }
          }, 5000)
        }
      }
    }
  }

  connectGame(gameId, onMessage) {
    if (this.gameSockets[gameId]) {
      if (this.gameSockets[gameId].readyState === WebSocket.OPEN) {
        console.log(`Game ${gameId} WebSocket already connected`)
        return
      }
      this.gameSockets[gameId].close()
      delete this.gameSockets[gameId]
    }

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = window.location.host
    const wsUrl = `${wsProtocol}//${wsHost}/ws/game/${gameId}/`
    
    console.log(`Connecting to game WebSocket: ${wsUrl}`)
    const socket = new WebSocket(wsUrl)
    this.gameSockets[gameId] = socket
    
    socket.onopen = () => {
      console.log(`Game ${gameId} WebSocket connected`)
    }
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        console.log(`Game ${gameId} WebSocket message received:`, data)
        onMessage(data)
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }
    
    socket.onerror = (error) => {
      console.error('Game WebSocket error:', error)
    }
    
    socket.onclose = (event) => {
      delete this.gameSockets[gameId]
      if (event.code !== 1000 && event.code !== 1001) {
        if (!this.reconnectingGames[gameId]) {
          this.reconnectingGames[gameId] = true
          setTimeout(() => {
            delete this.reconnectingGames[gameId]
            if (!this.gameSockets[gameId]) {
              this.connectGame(gameId, onMessage)
            }
          }, 5000)
        }
      }
    }
  }

  disconnectLobby() {
    if (this.lobbySocket) {
      this.lobbySocket.close()
      this.lobbySocket = null
    }
  }

  disconnectGame(gameId) {
    if (this.gameSockets[gameId]) {
      this.gameSockets[gameId].close()
      delete this.gameSockets[gameId]
    }
  }

  disconnectAll() {
    this.disconnectLobby()
    Object.keys(this.gameSockets).forEach(gameId => {
      this.disconnectGame(gameId)
    })
  }
}

export default new WebSocketService()

