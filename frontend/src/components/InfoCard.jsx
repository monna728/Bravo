export default function InfoCard({ location }) {
  return (
    <div className="bg-white rounded-xl shadow-2xl p-4 w-56 text-sm pointer-events-none">
      <h3 className="font-bold text-gray-900 text-base mb-1">{location.name}</h3>
      <p className="text-gray-500 text-xs mb-3">{location.eventName}</p>

      {/* Demand Score */}
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs text-gray-500 uppercase tracking-wide">Demand Score</span>
        <span className="font-bold text-gray-900">{location.demandScore}<span className="text-gray-400 font-normal">/100</span></span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div
          className={`h-2 rounded-full ${
            location.demandScore >= 70 ? 'bg-red-500' :
            location.demandScore >= 40 ? 'bg-yellow-400' : 'bg-green-400'
          }`}
          style={{ width: `${location.demandScore}%` }}
        />
      </div>
    </div>
  );
}