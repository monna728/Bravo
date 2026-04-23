const BASE_URL =
  process.env.REACT_APP_API_BASE ||
  'https://pphhzz75g2.execute-api.us-east-1.amazonaws.com/dev';

/**
 * POST /predict — returns Crowd Demand Index predictions for a borough and date range.
 * @param {object} params
 * @param {string} params.borough              - e.g. "Manhattan"
 * @param {string} params.startDate            - "YYYY-MM-DD"
 * @param {string} params.endDate              - "YYYY-MM-DD"
 * @param {string} [params.timeOfDay]          - "morning" | "afternoon" | "evening" | "night" | "all"
 * @param {boolean} [params.compareAllBoroughs]
 * @param {object|null} [params.futureRegressors] - optional known future values
 */
export async function predictDemand({
  borough,
  startDate,
  endDate,
  timeOfDay = 'all',
  compareAllBoroughs = false,
  futureRegressors = null,
}) {
  const response = await fetch(`${BASE_URL}/predict`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      borough,
      start_date: startDate,
      end_date: endDate,
      time_of_day: timeOfDay,
      compare_all_boroughs: compareAllBoroughs,
      future_regressors: futureRegressors,
    }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}

/**
 * GET /retrieve — retrieve stored ADAGE data from S3.
 */
export async function retrieveEvents({ borough, startDate, endDate }) {
  const params = new URLSearchParams({
    borough,
    start_date: startDate,
    end_date: endDate,
    processed: 'true',
  });
  const response = await fetch(`${BASE_URL}/retrieve?${params}`);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
  return data;
}
