// Mock analytics data for ride-sharing demand intelligence

export const WEEKLY_DEMAND = [
  { day: 'Mon', rides: 4200, revenue: 18900, avgWait: 3.2 },
  { day: 'Tue', rides: 3800, revenue: 17100, avgWait: 2.9 },
  { day: 'Wed', rides: 4600, revenue: 20700, avgWait: 3.5 },
  { day: 'Thu', rides: 5100, revenue: 22950, avgWait: 4.1 },
  { day: 'Fri', rides: 7400, revenue: 33300, avgWait: 6.8 },
  { day: 'Sat', rides: 8200, revenue: 36900, avgWait: 7.4 },
  { day: 'Sun', rides: 5900, revenue: 26550, avgWait: 5.2 },
];

export const HOURLY_DEMAND = [
  { hour: '12am', demand: 12 }, { hour: '1am', demand: 8 },
  { hour: '2am', demand: 20 }, { hour: '3am', demand: 15 },
  { hour: '4am', demand: 6 }, { hour: '5am', demand: 10 },
  { hour: '6am', demand: 28 }, { hour: '7am', demand: 54 },
  { hour: '8am', demand: 82 }, { hour: '9am', demand: 68 },
  { hour: '10am', demand: 45 }, { hour: '11am', demand: 41 },
  { hour: '12pm', demand: 62 }, { hour: '1pm', demand: 58 },
  { hour: '2pm', demand: 47 }, { hour: '3pm', demand: 51 },
  { hour: '4pm', demand: 65 }, { hour: '5pm', demand: 88 },
  { hour: '6pm', demand: 95 }, { hour: '7pm', demand: 91 },
  { hour: '8pm', demand: 84 }, { hour: '9pm', demand: 76 },
  { hour: '10pm', demand: 62 }, { hour: '11pm', demand: 38 },
];

export const BOROUGH_BREAKDOWN = [
  { borough: 'Manhattan', rides: 18400, share: 46, trend: +8.2 },
  { borough: 'Brooklyn', rides: 9600, share: 24, trend: +3.1 },
  { borough: 'Queens', rides: 7200, share: 18, trend: -1.4 },
  { borough: 'Bronx', rides: 3600, share: 9, trend: +5.7 },
  { borough: 'Staten Island', rides: 1200, share: 3, trend: -0.8 },
];

export const MONTHLY_TREND = [
  { month: 'Oct', revenue: 142000 },
  { month: 'Nov', revenue: 138000 },
  { month: 'Dec', revenue: 175000 },
  { month: 'Jan', revenue: 121000 },
  { month: 'Feb', revenue: 133000 },
  { month: 'Mar', revenue: 158000 },
];

export const EVENT_IMPACT = [
  { type: 'Sports', avgLift: 62, events: 14, topVenue: 'Yankee Stadium' },
  { type: 'Concerts', avgLift: 78, events: 9, topVenue: 'Madison Square Garden' },
  { type: 'Festivals', avgLift: 34, events: 6, topVenue: 'Flushing Meadows' },
];

export const KPI_CARDS = [
  { label: 'Total Rides (7d)', value: '39,200', change: +6.4, unit: '' },
  { label: 'Avg Revenue/Ride', value: '$4.50', change: +2.1, unit: '' },
  { label: 'Driver Utilisation', value: '74%', change: -1.2, unit: '' },
  { label: 'Avg Wait Time', value: '4.7 min', change: -8.3, unit: '' },
];

export const AI_INSIGHTS = [
  {
    id: 1,
    type: 'opportunity',
    title: 'Friday Night Surge Underserved',
    body: 'Friday 8–11pm demand is 34% above driver supply in Manhattan. Deploying 40+ additional drivers could recover an estimated $12,400 in weekly revenue.',
    icon: '⚡',
  },
  {
    id: 2,
    type: 'warning',
    title: 'Queens Demand Declining',
    body: 'Rides in Queens have dropped 1.4% week-over-week for 3 consecutive weeks. Possible competition or route changes warrant investigation.',
    icon: '⚠️',
  },
  {
    id: 3,
    type: 'info',
    title: 'Sports Events Drive 62% Demand Lift',
    body: 'Yankee Stadium and MSG events consistently produce the highest demand spikes. Pre-positioning drivers 45 minutes before events yields best response times.',
    icon: '🏟️',
  },
  {
    id: 4,
    type: 'opportunity',
    title: '6–8am Commute Window Underutilised',
    body: 'Morning commute rides are up 22% YoY but driver availability lags by ~18%. Incentivising early shifts could capture this growing segment.',
    icon: '🌅',
  },
];
