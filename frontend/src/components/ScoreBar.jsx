export default function ScoreBar({ score }) {
  const pct = Math.min(Math.max(score || 0, 0), 100)

  return (
    <div className="score-bar">
      <div className="score-bar__track">
        <div
          className="score-bar__fill"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="score-bar__value">{pct}</span>
    </div>
  )
}
