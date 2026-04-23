/**
 * PredictionResult — displays the output of a /predict API call.
 *
 * Props:
 *   result  — the full API response object from predictDemand()
 */

function cdiColor(score) {
  if (score >= 67) return { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-600', bar: '#ef4444', label: 'High Demand' };
  if (score >= 34) return { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-600', bar: '#f59e0b', label: 'Moderate Demand' };
  return { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-600', bar: '#10b981', label: 'Low Demand' };
}

function ScoreGauge({ score }) {
  const { bg, border, text, bar, label } = cdiColor(score);
  return (
    <div className={`rounded-2xl border p-5 text-center ${bg} ${border}`}>
      <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">Crowd Demand Index</p>
      <p className={`text-6xl font-black ${text}`}>{score}</p>
      <p className={`text-sm font-semibold mt-1 ${text}`}>{label}</p>
      {/* gauge bar */}
      <div className="mt-3 w-full bg-gray-100 rounded-full h-2">
        <div
          className="h-2 rounded-full transition-all duration-700"
          style={{ width: `${score}%`, backgroundColor: bar }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-400 mt-1">
        <span>0</span><span>50</span><span>100</span>
      </div>
    </div>
  );
}

function DayCard({ prediction }) {
  const { bg, border, text, bar } = cdiColor(prediction.crowd_demand_index);
  const cdi = prediction.crowd_demand_index;
  return (
    <div className={`rounded-xl border p-3 ${bg} ${border}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-semibold text-gray-600">{prediction.date}</span>
        <span className={`text-lg font-black ${text}`}>{cdi}</span>
      </div>
      <div className="w-full bg-white bg-opacity-60 rounded-full h-1.5">
        <div className="h-1.5 rounded-full" style={{ width: `${cdi}%`, backgroundColor: bar }} />
      </div>
      <div className="flex justify-between text-xs text-gray-400 mt-1">
        <span>↓ {prediction.lower_bound}</span>
        <span>↑ {prediction.upper_bound}</span>
      </div>
    </div>
  );
}

function ContributingFactors({ cf }) {
  if (!cf) return null;
  const taxiPct  = Math.round((cf.taxi_signal || 0) * 100);
  const eventPct = Math.round((cf.event_signal || 0) * 100);
  const regressorsUsed    = cf.regressors_used    || [];
  const regressorsSkipped = cf.regressors_skipped || [];
  const eventNames        = cf.active_event_names || [];

  return (
    <div className="space-y-3">
      {/* Taxi signal */}
      <div>
        <div className="flex justify-between text-xs mb-1">
          <span className="font-semibold text-gray-600">Taxi Signal</span>
          <span className="text-blue-500 font-bold">{taxiPct}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-1.5">
          <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${taxiPct}%` }} />
        </div>
      </div>

      {/* Event signal */}
      <div>
        <div className="flex justify-between text-xs mb-1">
          <span className="font-semibold text-gray-600">Event Signal</span>
          <span className="text-purple-500 font-bold">{eventPct}%</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-1.5">
          <div className="h-1.5 rounded-full bg-purple-500" style={{ width: `${eventPct}%` }} />
        </div>
      </div>

      {/* Weather impact */}
      <div className="flex justify-between items-center text-xs">
        <span className="font-semibold text-gray-600">Weather Impact</span>
        <span className={`font-semibold px-2 py-0.5 rounded-full text-xs ${
          cf.weather_impact_label === 'negative' ? 'bg-red-100 text-red-600' :
          cf.weather_impact_label === 'positive' ? 'bg-green-100 text-green-600' :
          'bg-gray-100 text-gray-500'
        }`}>
          {cf.weather_impact_label || 'neutral'}
        </span>
      </div>

      {/* Active events */}
      {eventNames.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-600 mb-1">Active Events</p>
          <div className="space-y-1">
            {eventNames.slice(0, 3).map((name, i) => (
              <div key={i} className="text-xs text-gray-500 bg-gray-50 rounded-lg px-2 py-1">
                {name}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Regressors */}
      {regressorsUsed.length > 0 && (
        <div className="pt-2 border-t border-gray-100">
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-1">
            Model Inputs Used
          </p>
          <div className="flex flex-wrap gap-1">
            {regressorsUsed.map((r) => (
              <span key={r} className="text-xs bg-blue-50 text-blue-600 border border-blue-100 px-2 py-0.5 rounded-full">
                {r}
              </span>
            ))}
          </div>
          {regressorsSkipped.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1">
              {regressorsSkipped.map((r) => (
                <span key={r} className="text-xs bg-gray-50 text-gray-400 border border-gray-100 px-2 py-0.5 rounded-full line-through">
                  {r}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function PredictionResult({ result }) {
  if (!result) return null;

  const predictions = result.predictions || [];
  if (!predictions.length) return null;

  const isSingleDay = predictions.length === 1;
  const firstPred   = predictions[0];
  const avgCDI      = Math.round(
    predictions.reduce((s, p) => s + p.crowd_demand_index, 0) / predictions.length
  );
  const displayCDI  = isSingleDay ? firstPred.crowd_demand_index : avgCDI;
  const cf          = result.contributing_factors || firstPred.contributing_factors;

  return (
    <div className="space-y-4 mt-4">
      {/* Score gauge — single day shows that day, multi-day shows average */}
      <ScoreGauge score={displayCDI} />

      {/* Multi-day: individual day cards */}
      {!isSingleDay && (
        <div>
          <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-2">
            Daily Breakdown
          </p>
          <div className="grid grid-cols-2 gap-2">
            {predictions.map((p) => (
              <DayCard key={p.date} prediction={p} />
            ))}
          </div>
        </div>
      )}

      {/* Single-day confidence band */}
      {isSingleDay && (
        <div className="flex justify-between text-xs text-gray-500 bg-gray-50 rounded-xl px-4 py-2">
          <span>Confidence: <strong>{Math.round((firstPred.confidence || 0) * 100)}%</strong></span>
          <span>Range: <strong>{firstPred.lower_bound} – {firstPred.upper_bound}</strong></span>
          <span>Weather: <strong>{firstPred.weather_condition || 'unknown'}</strong></span>
        </div>
      )}

      {/* Contributing factors */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
          Signal Breakdown
        </p>
        <ContributingFactors cf={cf} />
      </div>

      {/* Model info footnote */}
      {result.model_info && (
        <p className="text-xs text-gray-400 text-center">
          Trained on {result.model_info.training_days} days · {result.borough}
          {result.status === 'warning' && (
            <span className="text-amber-500"> · {result.message}</span>
          )}
        </p>
      )}
    </div>
  );
}
