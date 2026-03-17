export const LOCATIONS = [
  {
    id: 1,
    name: 'Times Square',
    position: { lat: 40.7580, lng: -73.9855 },
    type: 'concert',
    borough: 'Manhattan',
    eventName: 'Rock Concert',
    demandScore: 85,
    time: '20:00',
  },
  {
    id: 2,
    name: 'Barclays Center',
    position: { lat: 40.6826, lng: -73.9754 },
    type: 'sports',
    borough: 'Brooklyn',
    eventName: 'Nets vs Knicks',
    demandScore: 72,
    time: '19:30',
  },
  {
    id: 3,
    name: 'Flushing Meadows',
    position: { lat: 40.7282, lng: -73.8456 },
    type: 'festival',
    borough: 'Queens',
    eventName: 'Spring Cultural Festival',
    demandScore: 45,
    time: '10:00',
  },
  {
    id: 4,
    name: 'Yankee Stadium',
    position: { lat: 40.8296, lng: -73.9262 },
    type: 'sports',
    borough: 'Bronx',
    eventName: 'Yankees vs Red Sox',
    demandScore: 91,
    time: '18:00',
  },
  {
    id: 5,
    name: 'St. George Theatre',
    position: { lat: 40.6436, lng: -74.0764 },
    type: 'concert',
    borough: 'Staten Island',
    eventName: 'Jazz Night',
    demandScore: 30,
    time: '21:00',
  },
  {
    id: 6,
    name: 'Madison Square Garden',
    position: { lat: 40.7505, lng: -73.9934 },
    type: 'sports',
    borough: 'Manhattan',
    eventName: 'Rangers vs Bruins',
    demandScore: 78,
    time: '19:00',
  },
  {
    id: 7,
    name: 'Brooklyn Museum',
    position: { lat: 40.6712, lng: -73.9636 },
    type: 'festival',
    borough: 'Brooklyn',
    eventName: 'Art After Dark',
    demandScore: 55,
    time: '18:00',
  },
];

export const BOROUGHS = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'];
export const EVENT_TYPES = ['concert', 'sports', 'festival'];

export const TYPE_COLORS = {
  concert: 'bg-purple-500',
  sports: 'bg-blue-500',
  festival: 'bg-green-500',
};

export const TYPE_TEXT_COLORS = {
  concert: 'text-purple-600',
  sports: 'text-blue-600',
  festival: 'text-green-600',
};

export const TYPE_BG_LIGHT = {
  concert: 'bg-purple-50',
  sports: 'bg-blue-50',
  festival: 'bg-green-50',
};