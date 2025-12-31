import './ChessBoard.css'

function ChessBoard({ boardDict }) {
  const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
  const ranks = ['8', '7', '6', '5', '4', '3', '2', '1']

  const getSquareColor = (file, rank) => {
    const fileIndex = files.indexOf(file)
    const rankIndex = ranks.indexOf(rank)
    return (fileIndex + rankIndex) % 2 === 0 ? 'chocolate' : 'tan'
  }

  return (
    <div className="board-section">
      <div className="chess-board-container">
        <div className="row-numbers">
          {ranks.map((rank) => (
            <div key={rank} className="row-number">
              {rank}
            </div>
          ))}
        </div>
        <div className="chess-board">
          {ranks.map((rank) =>
            files.map((file) => {
              const square = `${file}${rank}`
              const piece = boardDict[square] || ''
              const squareColor = getSquareColor(file, rank)

              return (
                <div
                  key={square}
                  className="square"
                  style={{ backgroundColor: squareColor }}
                  dangerouslySetInnerHTML={{ __html: piece }}
                />
              )
            })
          )}
        </div>
      </div>
      <div className="column-letters">
        {files.map((file) => (
          <div key={file} className="column-letter">
            {file}
          </div>
        ))}
      </div>
    </div>
  )
}

export default ChessBoard

