// ─── Per-range analytics data ─────────────────────────────────────────────────

export const RANGE_DATA = {
  '7d': {
    label: 'Last 7 Days',
    compareLabel: 'vs prior 7 days',
    kpis: [
      { label: 'Total Rides', value: '39,200', change: +6.4 },
      { label: 'Avg Revenue / Ride', value: '$4.50', change: +2.1 },
      { label: 'Driver Utilisation', value: '74%', change: -1.2 },
      { label: 'Avg Wait Time', value: '4.7 min', change: -8.3 },
    ],
    barChart: {
      title: 'Rides by Day',
      subtitle: 'This week vs last week',
      data: [
        { label: 'Mon', rides: 4200, revenue: 18900 },
        { label: 'Tue', rides: 3800, revenue: 17100 },
        { label: 'Wed', rides: 4600, revenue: 20700 },
        { label: 'Thu', rides: 5100, revenue: 22950 },
        { label: 'Fri', rides: 7400, revenue: 33300 },
        { label: 'Sat', rides: 8200, revenue: 36900 },
        { label: 'Sun', rides: 5900, revenue: 26550 },
      ],
    },
    trendChart: {
      title: 'Daily Revenue',
      subtitle: 'Gross revenue each day this week',
      data: [
        { label: 'Mon', value: 18900 },
        { label: 'Tue', value: 17100 },
        { label: 'Wed', value: 20700 },
        { label: 'Thu', value: 22950 },
        { label: 'Fri', value: 33300 },
        { label: 'Sat', value: 36900 },
        { label: 'Sun', value: 26550 },
      ],
    },
    hourly: [12,8,20,15,6,10,28,54,82,68,45,41,62,58,47,51,65,88,95,91,84,76,62,38],
    boroughs: [
      { borough: 'Manhattan', share: 46, trend: +8.2 },
      { borough: 'Brooklyn',  share: 24, trend: +3.1 },
      { borough: 'Queens',    share: 18, trend: -1.4 },
      { borough: 'Bronx',     share: 9,  trend: +5.7 },
      { borough: 'Staten Is.',share: 3,  trend: -0.8 },
    ],
    events: [
      { type: 'Sports',   avgLift: 62, count: 14, topVenue: 'Yankee Stadium' },
      { type: 'Concerts', avgLift: 78, count: 9,  topVenue: 'Madison Sq. Garden' },
      { type: 'Festivals',avgLift: 34, count: 6,  topVenue: 'Flushing Meadows' },
    ],
    insights: [
      { id: 1, type: 'opportunity', icon: '⚡', title: 'Friday Night Surge Underserved', body: 'Friday 8–11pm demand is 34% above driver supply in Manhattan. Deploying 40+ additional drivers could recover ~$12,400 in weekly revenue.' },
      { id: 2, type: 'warning',     icon: '⚠️', title: 'Queens Demand Declining',        body: 'Rides in Queens dropped 1.4% WoW for the 3rd straight week. Possible competition or seasonal factors warrant investigation.' },
      { id: 3, type: 'info',        icon: '🏟️', title: 'Concerts Drive Highest Lift (+78%)', body: 'Concert events at MSG consistently produce the highest demand spikes. Pre-positioning drivers 45 min before showtime yields the best response times.' },
    ],
    aiSummary: `This week delivered solid top-line growth with 39,200 total rides — up 6.4% on the prior week — generating an average of $4.50 per ride. Saturday peaked at 8,200 rides, driven by a combination of sports fixtures and two major concerts. Revenue per ride ticked up 2.1%, and the average wait time fell to 4.7 minutes, signalling improving dispatch efficiency across most zones.\n\nThe most pressing opportunity remains Friday evening supply gaps. Demand between 8pm and 11pm consistently outpaces driver availability by around 34% in Manhattan, leaving significant revenue on the table. Queens continues to soften — three consecutive weeks of decline point to either competitive pressure or seasonal factors that need closer examination before they compound further.\n\nImmediate priorities: incentivise Friday late-night driver shifts in Manhattan, flag Queens for a route-level audit, and pre-deploy drivers around MSG and Barclays on concert nights. Targeting these three actions alone could recover an estimated $15,000–$18,000 in weekly revenue.`,
  },

  '30d': {
    label: 'Last 30 Days',
    compareLabel: 'vs prior 30 days',
    kpis: [
      { label: 'Total Rides', value: '164,800', change: +11.2 },
      { label: 'Avg Revenue / Ride', value: '$4.62', change: +4.5 },
      { label: 'Driver Utilisation', value: '71%', change: -3.8 },
      { label: 'Avg Wait Time', value: '5.1 min', change: +2.0 },
    ],
    barChart: {
      title: 'Rides by Week',
      subtitle: 'Weekly totals over the last 4 weeks',
      data: [
        { label: 'Wk 1', rides: 36400, revenue: 168000 },
        { label: 'Wk 2', rides: 38900, revenue: 179700 },
        { label: 'Wk 3', rides: 41200, revenue: 190300 },
        { label: 'Wk 4', rides: 48300, revenue: 223100 },
      ],
    },
    trendChart: {
      title: 'Weekly Revenue Trend',
      subtitle: 'Gross revenue by week',
      data: [
        { label: 'Wk 1', value: 168000 },
        { label: 'Wk 2', value: 179700 },
        { label: 'Wk 3', value: 190300 },
        { label: 'Wk 4', value: 223100 },
      ],
    },
    hourly: [14,9,22,17,7,12,31,57,79,71,50,44,65,61,50,55,68,85,92,88,80,72,58,34],
    boroughs: [
      { borough: 'Manhattan', share: 47, trend: +11.8 },
      { borough: 'Brooklyn',  share: 23, trend: +6.2  },
      { borough: 'Queens',    share: 19, trend: -3.1  },
      { borough: 'Bronx',     share: 8,  trend: +9.3  },
      { borough: 'Staten Is.',share: 3,  trend: -1.5  },
    ],
    events: [
      { type: 'Sports',   avgLift: 58, count: 52, topVenue: 'Yankee Stadium' },
      { type: 'Concerts', avgLift: 74, count: 31, topVenue: 'Madison Sq. Garden' },
      { type: 'Festivals',avgLift: 41, count: 18, topVenue: 'Flushing Meadows' },
    ],
    insights: [
      { id: 1, type: 'opportunity', icon: '📈', title: 'Month-on-Month Growth Accelerating',  body: 'Week 4 outperformed Week 1 by 32.7% in rides — the strongest intra-month acceleration in 6 months. Growth is compounding, not plateauing.' },
      { id: 2, type: 'warning',     icon: '⚠️', title: 'Driver Utilisation Slipping',         body: 'Utilisation fell 3.8% over 30 days despite rising demand. Fleet growth is outpacing optimisation — idle driver time increased in Brooklyn and Staten Island.' },
      { id: 3, type: 'info',        icon: '🗺️', title: 'Bronx Emerging as Growth Zone',       body: 'The Bronx posted +9.3% growth over 30 days — second only to Manhattan. Increased sports event coverage around Yankee Stadium is a key driver.' },
    ],
    aiSummary: `The 30-day period shows a clear upward trajectory: 164,800 total rides at an average of $4.62 — up 4.5% on the prior month — with the strongest week landing in the final seven days at 48,300 rides. This accelerating intra-month trend suggests demand momentum is building rather than levelling off, which is a strong signal heading into the next quarter.\n\nThe headline risk is driver utilisation, which slipped 3.8% to 71% over the period. Fleet supply is growing faster than dispatch efficiency, particularly in Brooklyn and Staten Island where idle time has increased. Wait times edged up 2.0% as a result — a trend that, if sustained, risks eroding rider satisfaction scores. Queens continues its decline at -3.1% over 30 days, pointing to structural rather than seasonal softness.\n\nPriority actions for the next 30 days: tighten dispatch logic in outer boroughs to recover utilisation, run a targeted rider retention campaign in Queens, and increase driver incentives in the Bronx to capitalise on its +9.3% growth momentum. Protecting the Friday–Saturday surge window with pre-committed driver supply should remain a standing operational priority.`,
  },

  '90d': {
    label: 'Last 90 Days',
    compareLabel: 'vs prior 90 days',
    kpis: [
      { label: 'Total Rides', value: '471,000', change: +18.7 },
      { label: 'Avg Revenue / Ride', value: '$4.71', change: +7.3 },
      { label: 'Driver Utilisation', value: '69%', change: -5.5 },
      { label: 'Avg Wait Time', value: '5.4 min', change: +5.9 },
    ],
    barChart: {
      title: 'Rides by Month',
      subtitle: 'Monthly totals over last 3 months',
      data: [
        { label: 'Jan', rides: 138000, revenue: 649800 },
        { label: 'Feb', rides: 152000, revenue: 715600 },
        { label: 'Mar', rides: 181000, revenue: 852300 },
      ],
    },
    trendChart: {
      title: 'Quarterly Revenue Trend',
      subtitle: 'Monthly gross revenue',
      data: [
        { label: 'Jan', value: 649800 },
        { label: 'Feb', value: 715600 },
        { label: 'Mar', value: 852300 },
      ],
    },
    hourly: [16,10,24,18,8,15,35,61,76,74,54,48,67,63,53,57,70,83,90,86,78,70,55,30],
    boroughs: [
      { borough: 'Manhattan', share: 47, trend: +20.4 },
      { borough: 'Brooklyn',  share: 23, trend: +14.7 },
      { borough: 'Queens',    share: 19, trend: -4.8  },
      { borough: 'Bronx',     share: 8,  trend: +22.1 },
      { borough: 'Staten Is.',share: 3,  trend: -2.3  },
    ],
    events: [
      { type: 'Sports',   avgLift: 55, count: 148, topVenue: 'Yankee Stadium' },
      { type: 'Concerts', avgLift: 72, count: 89,  topVenue: 'Madison Sq. Garden' },
      { type: 'Festivals',avgLift: 38, count: 44,  topVenue: 'Flushing Meadows' },
    ],
    insights: [
      { id: 1, type: 'opportunity', icon: '🚀', title: 'Bronx Up +22% — Fleet Under-Indexed',   body: 'The Bronx is the fastest-growing borough over 90 days at +22.1%, yet driver density remains 40% below Manhattan per km². A targeted fleet expansion could unlock significant upside.' },
      { id: 2, type: 'warning',     icon: '⚠️', title: 'Queens Lost 4.8% Over the Quarter',    body: 'Queens has declined consistently across all three months. Competitive intelligence suggests a rival operator expanded in Flushing and Jamaica — strategic response needed.' },
      { id: 3, type: 'info',        icon: '📅', title: 'March Best Month in 18 Months',         body: 'March delivered 181,000 rides and $852K gross revenue — the highest single-month figures in a year and a half. A dense event calendar was the primary catalyst.' },
    ],
    aiSummary: `Over the 90-day period, the platform processed 471,000 rides at $4.71 average revenue — an 18.7% volume increase and 7.3% revenue-per-ride improvement versus the prior quarter. March was the standout month at 181,000 rides and $852K gross, the strongest single month in 18 months, fuelled by a dense calendar of sports and concert events across Manhattan and Brooklyn. The trajectory across all three months is consistently upward, confirming that demand fundamentals are robust.\n\nHowever, structural cracks are widening. Driver utilisation has declined 5.5 percentage points to 69%, and average wait times are up 5.9% — both pointing to a fleet allocation problem rather than a supply shortage. Queens has lost 4.8% of rides against what appears to be deliberate competitor expansion in Flushing and Jamaica. Left unaddressed, this erosion will compound into Q2. The Bronx presents the sharpest contrast: +22.1% growth with driver density still 40% below Manhattan, making it the clearest under-served opportunity in the network.\n\nStrategic priorities for Q2: reallocate fleet capacity toward the Bronx and high-density Manhattan corridors, launch a Queens-specific retention and pricing review, and invest in dispatch algorithm improvements to recover utilisation toward the 75–78% target range. Sustaining the event-driven demand peaks that powered March will require proactive driver pre-positioning protocols to become standard operating procedure.`,
  },
};
