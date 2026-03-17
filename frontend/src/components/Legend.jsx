export default function Legend() {
  return (
    <div className="absolute bottom-8 left-4 z-10 bg-white rounded-2xl shadow-lg p-4 w-44">
      <h2 className="font-semibold text-gray-800 text-sm mb-3">Demand Score</h2>

      {/* Gradient bar */}
      <div
        className="w-full h-3 rounded-full mb-1"
        style={{
          background: 'linear-gradient(to right, #4ade80, #facc15, #ef4444)',
        }}
      />

      {/* Labels */}
      <div className="flex justify-between text-xs text-gray-400">
        <span>Low</span>
        <span>Mid</span>
        <span>High</span>
      </div>

      {/* Tick labels */}
      <div className="flex justify-between text-xs text-gray-300 mt-0.5">
        <span>0</span>
        <span>50</span>
        <span>100</span>
      </div>
    </div>
  );
}