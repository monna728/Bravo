export const BOROUGH_NEIGHBOURHOODS = {
  Manhattan:     ['Midtown', 'Chelsea', 'Lower Manhattan', 'Upper East Side', 'Harlem', 'Hell\'s Kitchen', 'Greenwich Village', 'Tribeca/SoHo'],
  Brooklyn:      ['Downtown Brooklyn', 'Williamsburg', 'Park Slope', 'Bushwick', 'DUMBO', 'Crown Heights', 'Bay Ridge', 'Greenpoint'],
  Queens:        ['Flushing', 'Astoria', 'Long Island City', 'Jamaica', 'Forest Hills', 'Jackson Heights'],
  Bronx:         ['Fordham', 'Mott Haven', 'Pelham Bay', 'Riverdale', 'South Bronx'],
  'Staten Island': ['St. George', 'Stapleton', 'New Dorp', 'Tottenville'],
};

export const LOCATIONS = [
  // ── Apr 15 ──────────────────────────────────────────────────────────────────
  { id: 1,  name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Red Sox',               demandScore: 91, time: '13:05', date: '2026-04-15' },
  { id: 2,  name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Sabrina Carpenter – Tour',         demandScore: 88, time: '20:00', date: '2026-04-15' },
  { id: 3,  name: 'Brooklyn Museum',       position: { lat: 40.6712, lng: -73.9636 }, type: 'festival', borough: 'Brooklyn',       neighbourhood: 'Park Slope',         eventName: 'First Saturday Night',             demandScore: 52, time: '17:00', date: '2026-04-15' },
  { id: 4,  name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets Home Opener',                 demandScore: 80, time: '13:10', date: '2026-04-15' },
  { id: 5,  name: 'Empire Outlets',        position: { lat: 40.6436, lng: -74.0731 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'St. George',         eventName: 'Spring Market Weekend',            demandScore: 38, time: '11:00', date: '2026-04-15' },

  // ── Apr 16 ──────────────────────────────────────────────────────────────────
  { id: 6,  name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Red Sox',               demandScore: 78, time: '19:05', date: '2026-04-16' },
  { id: 7,  name: 'Barclays Center',       position: { lat: 40.6826, lng: -73.9754 }, type: 'sports',   borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'Nets vs Celtics – Playoffs',       demandScore: 87, time: '20:30', date: '2026-04-16' },
  { id: 8,  name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Phillies',                 demandScore: 74, time: '19:10', date: '2026-04-16' },
  { id: 9,  name: 'Times Square',          position: { lat: 40.7580, lng: -73.9855 }, type: 'festival', borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Spring Street Fair',               demandScore: 55, time: '12:00', date: '2026-04-16' },
  { id: 10, name: 'SI Yankees Stadium',    position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees – Home Opener',         demandScore: 45, time: '18:00', date: '2026-04-16' },

  // ── Apr 17 ──────────────────────────────────────────────────────────────────
  { id: 11, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'sports',   borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Rangers vs Bruins – Game 1',       demandScore: 85, time: '19:00', date: '2026-04-17' },
  { id: 12, name: 'Flushing Meadows Park', position: { lat: 40.7282, lng: -73.8456 }, type: 'festival', borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Queens Spring Fair',               demandScore: 41, time: '11:00', date: '2026-04-17' },
  { id: 13, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Red Sox',               demandScore: 83, time: '13:05', date: '2026-04-17' },
  { id: 14, name: 'Barclays Center',       position: { lat: 40.6826, lng: -73.9754 }, type: 'sports',   borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'Nets vs Celtics – Game 1',         demandScore: 82, time: '13:00', date: '2026-04-17' },
  { id: 15, name: 'SI Museum',             position: { lat: 40.6419, lng: -74.0748 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'St. George',         eventName: 'Art & Heritage Night',             demandScore: 30, time: '18:00', date: '2026-04-17' },

  // ── Apr 18 ──────────────────────────────────────────────────────────────────
  { id: 16, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Blue Jays',             demandScore: 89, time: '19:05', date: '2026-04-18' },
  { id: 17, name: 'Brooklyn Steel',        position: { lat: 40.7207, lng: -73.9340 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Williamsburg',       eventName: 'Jungle – Live',                    demandScore: 63, time: '21:00', date: '2026-04-18' },
  { id: 18, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Phillies',                 demandScore: 71, time: '19:10', date: '2026-04-18' },
  { id: 19, name: 'Times Square',          position: { lat: 40.7580, lng: -73.9855 }, type: 'festival', borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Weekend Street Market',            demandScore: 48, time: '13:00', date: '2026-04-18' },
  { id: 20, name: 'Snug Harbor',           position: { lat: 40.6437, lng: -74.1003 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'Spring Botanical Fair',            demandScore: 42, time: '11:00', date: '2026-04-18' },

  // ── Apr 19 ──────────────────────────────────────────────────────────────────
  { id: 21, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Bad Bunny – World Tour',           demandScore: 95, time: '20:30', date: '2026-04-19' },
  { id: 22, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Phillies',                 demandScore: 71, time: '13:10', date: '2026-04-19' },
  { id: 23, name: 'Barclays Center',       position: { lat: 40.6826, lng: -73.9754 }, type: 'sports',   borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'Nets vs Celtics – Game 2',         demandScore: 84, time: '20:00', date: '2026-04-19' },
  { id: 24, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Blue Jays',             demandScore: 77, time: '19:05', date: '2026-04-19' },
  { id: 25, name: 'SI Yankees Stadium',    position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees Game',                  demandScore: 43, time: '18:00', date: '2026-04-19' },

  // ── Apr 20 ──────────────────────────────────────────────────────────────────
  { id: 26, name: 'Barclays Center',       position: { lat: 40.6826, lng: -73.9754 }, type: 'sports',   borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'Nets vs Celtics – Game 3',         demandScore: 90, time: '13:00', date: '2026-04-20' },
  { id: 27, name: 'Prospect Park',         position: { lat: 40.6602, lng: -73.9690 }, type: 'festival', borough: 'Brooklyn',       neighbourhood: 'Park Slope',         eventName: 'Earth Day Festival',               demandScore: 58, time: '10:00', date: '2026-04-20' },
  { id: 28, name: 'Times Square',          position: { lat: 40.7580, lng: -73.9855 }, type: 'festival', borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Earth Day Block Party',            demandScore: 67, time: '12:00', date: '2026-04-20' },
  { id: 29, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Blue Jays',             demandScore: 72, time: '13:05', date: '2026-04-20' },
  { id: 30, name: 'Jackson Heights Plaza', position: { lat: 40.7484, lng: -73.8915 }, type: 'festival', borough: 'Queens',         neighbourhood: 'Jackson Heights',    eventName: 'Earth Day Community Fair',         demandScore: 44, time: '11:00', date: '2026-04-20' },
  { id: 31, name: 'Snug Harbor',           position: { lat: 40.6437, lng: -74.1003 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'Earth Day Spring Fest',            demandScore: 48, time: '10:00', date: '2026-04-20' },

  // ── Apr 21 ──────────────────────────────────────────────────────────────────
  { id: 32, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'sports',   borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Rangers vs Bruins – Game 2',       demandScore: 86, time: '19:00', date: '2026-04-21' },
  { id: 33, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Braves',                   demandScore: 68, time: '19:10', date: '2026-04-21' },
  { id: 34, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Orioles',               demandScore: 74, time: '19:05', date: '2026-04-21' },
  { id: 35, name: 'Barclays Center',       position: { lat: 40.6826, lng: -73.9754 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'Weekend Club Night',               demandScore: 60, time: '22:00', date: '2026-04-21' },
  { id: 36, name: 'SI Yankees Stadium',    position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees Game',                  demandScore: 41, time: '18:00', date: '2026-04-21' },

  // ── Apr 22 ──────────────────────────────────────────────────────────────────
  { id: 37, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Orioles',               demandScore: 78, time: '19:05', date: '2026-04-22' },
  { id: 38, name: 'Brooklyn Mirage',       position: { lat: 40.6938, lng: -73.9299 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Bushwick',           eventName: 'Fred Again – Opening Night',       demandScore: 82, time: '22:00', date: '2026-04-22' },
  { id: 39, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Braves',                   demandScore: 66, time: '13:10', date: '2026-04-22' },
  { id: 40, name: 'Times Square',          position: { lat: 40.7580, lng: -73.9855 }, type: 'festival', borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Broadway Week Kickoff',            demandScore: 62, time: '18:00', date: '2026-04-22' },
  { id: 41, name: 'Empire Outlets',        position: { lat: 40.6436, lng: -74.0731 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'St. George',         eventName: 'Weekend Shopping Event',           demandScore: 35, time: '11:00', date: '2026-04-22' },

  // ── Apr 24 ──────────────────────────────────────────────────────────────────
  { id: 42, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Mariners',              demandScore: 75, time: '19:05', date: '2026-04-24' },
  { id: 43, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Braves',                   demandScore: 69, time: '19:10', date: '2026-04-24' },
  { id: 44, name: 'Kings Theatre',         position: { lat: 40.6519, lng: -73.9495 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Crown Heights',      eventName: 'LCD Soundsystem',                  demandScore: 71, time: '20:00', date: '2026-04-24' },
  { id: 45, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Jazz at MSG',                      demandScore: 58, time: '19:30', date: '2026-04-24' },
  { id: 46, name: 'SI Yankees Stadium',    position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees Game',                  demandScore: 40, time: '18:00', date: '2026-04-24' },

  // ── Apr 25 ──────────────────────────────────────────────────────────────────
  { id: 47, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Mariners',              demandScore: 83, time: '13:05', date: '2026-04-25' },
  { id: 48, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Chappell Roan – Midwest Princess', demandScore: 93, time: '20:00', date: '2026-04-25' },
  { id: 49, name: 'Flushing Meadows Park', position: { lat: 40.7282, lng: -73.8456 }, type: 'festival', borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Queens International Food Fest',   demandScore: 56, time: '11:00', date: '2026-04-25' },
  { id: 50, name: 'Brooklyn Museum',       position: { lat: 40.6712, lng: -73.9636 }, type: 'festival', borough: 'Brooklyn',       neighbourhood: 'Park Slope',         eventName: 'First Saturday Night',             demandScore: 54, time: '17:00', date: '2026-04-25' },
  { id: 51, name: 'St. George Theatre',    position: { lat: 40.6436, lng: -74.0764 }, type: 'concert',  borough: 'Staten Island',  neighbourhood: 'St. George',         eventName: 'Comedy Night',                     demandScore: 37, time: '20:00', date: '2026-04-25' },

  // ── Apr 26 ──────────────────────────────────────────────────────────────────
  { id: 52, name: 'Barclays Center',       position: { lat: 40.6826, lng: -73.9754 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: "Drake – It's All a Blur Tour",     demandScore: 97, time: '20:00', date: '2026-04-26' },
  { id: 53, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Braves',                   demandScore: 73, time: '13:10', date: '2026-04-26' },
  { id: 54, name: 'St. George Theatre',    position: { lat: 40.6436, lng: -74.0764 }, type: 'concert',  borough: 'Staten Island',  neighbourhood: 'St. George',         eventName: 'Jazz & Blues Night',               demandScore: 38, time: '20:00', date: '2026-04-26' },
  { id: 55, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Mariners',              demandScore: 80, time: '19:05', date: '2026-04-26' },
  { id: 56, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Chappell Roan – Night 2',          demandScore: 91, time: '20:00', date: '2026-04-26' },

  // ── Apr 27 ──────────────────────────────────────────────────────────────────
  { id: 57, name: 'Barclays Center',       position: { lat: 40.6826, lng: -73.9754 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'Drake – Night 2',                  demandScore: 96, time: '20:00', date: '2026-04-27' },
  { id: 58, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'sports',   borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Rangers vs Hurricanes – Rd 2',     demandScore: 88, time: '19:30', date: '2026-04-27' },
  { id: 59, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Mariners',              demandScore: 76, time: '13:05', date: '2026-04-27' },
  { id: 60, name: 'Jackson Heights Plaza', position: { lat: 40.7484, lng: -73.8915 }, type: 'festival', borough: 'Queens',         neighbourhood: 'Jackson Heights',    eventName: 'Weekend Cultural Market',          demandScore: 46, time: '12:00', date: '2026-04-27' },
  { id: 61, name: 'Snug Harbor',           position: { lat: 40.6437, lng: -74.1003 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'Spring Concert Series',            demandScore: 44, time: '14:00', date: '2026-04-27' },

  // ── Apr 29 ──────────────────────────────────────────────────────────────────
  { id: 62, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Orioles',               demandScore: 76, time: '19:05', date: '2026-04-29' },
  { id: 63, name: 'Brooklyn Mirage',       position: { lat: 40.6938, lng: -73.9299 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Bushwick',           eventName: 'Four Tet – Live',                  demandScore: 79, time: '22:00', date: '2026-04-29' },
  { id: 64, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Cubs',                     demandScore: 67, time: '19:10', date: '2026-04-29' },
  { id: 65, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Tuesday Night Live',               demandScore: 54, time: '20:00', date: '2026-04-29' },
  { id: 66, name: 'SI Yankees Stadium',    position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees Game',                  demandScore: 41, time: '18:00', date: '2026-04-29' },

  // ── May 1 ───────────────────────────────────────────────────────────────────
  { id: 67, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Olivia Rodrigo – GUTS World Tour', demandScore: 94, time: '19:30', date: '2026-05-01' },
  { id: 68, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Dodgers',                  demandScore: 85, time: '19:10', date: '2026-05-01' },
  { id: 69, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Orioles',               demandScore: 73, time: '19:05', date: '2026-05-01' },
  { id: 70, name: 'Brooklyn Steel',        position: { lat: 40.7207, lng: -73.9340 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Williamsburg',       eventName: 'Floating Points – Live',           demandScore: 64, time: '21:00', date: '2026-05-01' },
  { id: 71, name: 'SI Yankees Stadium',    position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees Game',                  demandScore: 43, time: '18:00', date: '2026-05-01' },

  // ── May 2 ───────────────────────────────────────────────────────────────────
  { id: 72, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Dodgers',                  demandScore: 88, time: '13:10', date: '2026-05-02' },
  { id: 73, name: 'Barclays Center',       position: { lat: 40.6826, lng: -73.9754 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'Billie Eilish – Hit Me Hard',      demandScore: 96, time: '20:00', date: '2026-05-02' },
  { id: 74, name: 'Prospect Park',         position: { lat: 40.6602, lng: -73.9690 }, type: 'festival', borough: 'Brooklyn',       neighbourhood: 'Park Slope',         eventName: 'Cinco de Mayo Preview Fest',       demandScore: 48, time: '13:00', date: '2026-05-02' },
  { id: 75, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Royals',                demandScore: 77, time: '13:05', date: '2026-05-02' },
  { id: 76, name: 'Governors Island',      position: { lat: 40.6895, lng: -74.0166 }, type: 'festival', borough: 'Manhattan',      neighbourhood: 'Lower Manhattan',    eventName: 'Island Opening Weekend',           demandScore: 61, time: '11:00', date: '2026-05-02' },
  { id: 77, name: 'SI Half Marathon',      position: { lat: 40.6436, lng: -74.0748 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'St. George',         eventName: 'Staten Island Half Marathon',      demandScore: 55, time: '07:00', date: '2026-05-02' },

  // ── May 3 ───────────────────────────────────────────────────────────────────
  { id: 78, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Royals',                demandScore: 80, time: '13:05', date: '2026-05-03' },
  { id: 79, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'The Weeknd – After Hours Tour',    demandScore: 95, time: '21:00', date: '2026-05-03' },
  { id: 80, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Dodgers',                  demandScore: 82, time: '13:10', date: '2026-05-03' },
  { id: 81, name: 'Brooklyn Mirage',       position: { lat: 40.6938, lng: -73.9299 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Bushwick',           eventName: 'John Summit – Live',               demandScore: 75, time: '22:00', date: '2026-05-03' },
  { id: 82, name: 'Snug Harbor',           position: { lat: 40.6437, lng: -74.1003 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'Spring Garden Show',               demandScore: 45, time: '10:00', date: '2026-05-03' },

  // ── May 5 ───────────────────────────────────────────────────────────────────
  { id: 83, name: 'Times Square',          position: { lat: 40.7580, lng: -73.9855 }, type: 'festival', borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Cinco de Mayo Street Festival',    demandScore: 72, time: '14:00', date: '2026-05-05' },
  { id: 84, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Cubs',                     demandScore: 68, time: '19:10', date: '2026-05-05' },
  { id: 85, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Rangers',               demandScore: 75, time: '19:05', date: '2026-05-05' },
  { id: 86, name: 'Prospect Park',         position: { lat: 40.6602, lng: -73.9690 }, type: 'festival', borough: 'Brooklyn',       neighbourhood: 'Park Slope',         eventName: 'Cinco de Mayo Block Party',        demandScore: 62, time: '13:00', date: '2026-05-05' },
  { id: 87, name: 'Empire Outlets',        position: { lat: 40.6436, lng: -74.0731 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'St. George',         eventName: 'Cinco de Mayo Market',             demandScore: 46, time: '12:00', date: '2026-05-05' },

  // ── May 7 ───────────────────────────────────────────────────────────────────
  { id: 88, name: 'Barclays Center',       position: { lat: 40.6826, lng: -73.9754 }, type: 'sports',   borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'Nets vs Heat – Playoffs',          demandScore: 86, time: '20:00', date: '2026-05-07' },
  { id: 89, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Rangers',               demandScore: 82, time: '19:05', date: '2026-05-07' },
  { id: 90, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'sports',   borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Rangers – Conference Semis',       demandScore: 89, time: '19:00', date: '2026-05-07' },
  { id: 91, name: 'Citi Field',            position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Cubs',                     demandScore: 66, time: '13:10', date: '2026-05-07' },
  { id: 92, name: 'SI Yankees Stadium',    position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees Game',                  demandScore: 42, time: '18:00', date: '2026-05-07' },

  // ── May 9 ───────────────────────────────────────────────────────────────────
  { id: 93, name: 'Madison Square Garden', position: { lat: 40.7505, lng: -73.9934 }, type: 'sports',   borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Rangers – Conference Finals',      demandScore: 92, time: '20:00', date: '2026-05-09' },
  { id: 94, name: 'Brooklyn Steel',        position: { lat: 40.7207, lng: -73.9340 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Williamsburg',       eventName: 'Mk.gee – Live',                    demandScore: 55, time: '21:00', date: '2026-05-09' },
  { id: 95, name: 'Yankee Stadium',        position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs White Sox',             demandScore: 74, time: '19:05', date: '2026-05-09' },
  { id: 96, name: 'Flushing Meadows Park', position: { lat: 40.7282, lng: -73.8456 }, type: 'festival', borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Queens Night Market Opens',        demandScore: 62, time: '18:00', date: '2026-05-09' },
  { id: 97, name: 'SI Yankees Stadium',    position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees Game',                  demandScore: 43, time: '18:00', date: '2026-05-09' },

  // ── May 10 ──────────────────────────────────────────────────────────────────
  { id: 98,  name: 'Citi Field',           position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Cardinals',                demandScore: 66, time: '13:10', date: '2026-05-10' },
  { id: 99,  name: 'Governors Island',     position: { lat: 40.6895, lng: -74.0166 }, type: 'festival', borough: 'Manhattan',      neighbourhood: 'Lower Manhattan',    eventName: 'Jazz Age Lawn Party',              demandScore: 61, time: '12:00', date: '2026-05-10' },
  { id: 100, name: 'Yankee Stadium',       position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs White Sox',             demandScore: 71, time: '13:05', date: '2026-05-10' },
  { id: 101, name: 'Brooklyn Museum',      position: { lat: 40.6712, lng: -73.9636 }, type: 'festival', borough: 'Brooklyn',       neighbourhood: 'Park Slope',         eventName: 'First Saturday Night',             demandScore: 55, time: '17:00', date: '2026-05-10' },
  { id: 102, name: 'Snug Harbor',          position: { lat: 40.6437, lng: -74.1003 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'Spring Weekend Concert',           demandScore: 46, time: '14:00', date: '2026-05-10' },

  // ── May 14 ──────────────────────────────────────────────────────────────────
  { id: 103, name: 'Madison Square Garden',position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Kendrick Lamar – Grand National',  demandScore: 98, time: '20:30', date: '2026-05-14' },
  { id: 104, name: 'Yankee Stadium',       position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Tigers',                demandScore: 74, time: '19:05', date: '2026-05-14' },
  { id: 105, name: 'Barclays Center',      position: { lat: 40.6826, lng: -73.9754 }, type: 'sports',   borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'Nets – Conference Semis Gm 4',     demandScore: 88, time: '20:00', date: '2026-05-14' },
  { id: 106, name: 'Citi Field',           position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Giants',                   demandScore: 71, time: '19:10', date: '2026-05-14' },
  { id: 107, name: 'SI Museum',            position: { lat: 40.6419, lng: -74.0748 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'St. George',         eventName: 'Cultural Heritage Festival',       demandScore: 52, time: '12:00', date: '2026-05-14' },

  // ── May 15 ──────────────────────────────────────────────────────────────────
  { id: 108, name: 'Madison Square Garden',position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Kendrick Lamar – Night 2',         demandScore: 98, time: '20:30', date: '2026-05-15' },
  { id: 109, name: 'Barclays Center',      position: { lat: 40.6826, lng: -73.9754 }, type: 'sports',   borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'Nets – Conference Semis',          demandScore: 89, time: '20:00', date: '2026-05-15' },
  { id: 110, name: 'Prospect Park',        position: { lat: 40.6602, lng: -73.9690 }, type: 'festival', borough: 'Brooklyn',       neighbourhood: 'Park Slope',         eventName: 'Celebrate Brooklyn! Opening',      demandScore: 64, time: '18:00', date: '2026-05-15' },
  { id: 111, name: 'Yankee Stadium',       position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Tigers',                demandScore: 78, time: '19:05', date: '2026-05-15' },
  { id: 112, name: 'Citi Field',           position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Giants',                   demandScore: 73, time: '19:10', date: '2026-05-15' },
  { id: 113, name: 'SI Yankees Stadium',   position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees Game',                  demandScore: 41, time: '18:00', date: '2026-05-15' },

  // ── May 16 ──────────────────────────────────────────────────────────────────
  { id: 114, name: 'Citi Field',           position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Padres',                   demandScore: 77, time: '13:10', date: '2026-05-16' },
  { id: 115, name: 'Brooklyn Mirage',      position: { lat: 40.6938, lng: -73.9299 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Bushwick',           eventName: 'Disclosure – Live',                demandScore: 76, time: '22:00', date: '2026-05-16' },
  { id: 116, name: 'Yankee Stadium',       position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Athletics',             demandScore: 76, time: '13:05', date: '2026-05-16' },
  { id: 117, name: 'Governors Island',     position: { lat: 40.6895, lng: -74.0166 }, type: 'festival', borough: 'Manhattan',      neighbourhood: 'Lower Manhattan',    eventName: 'Jazz Age Lawn Party – Day 2',      demandScore: 59, time: '12:00', date: '2026-05-16' },
  { id: 118, name: 'SI Museum',            position: { lat: 40.6419, lng: -74.0748 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'St. George',         eventName: 'SI Arts & Culture Festival',       demandScore: 50, time: '11:00', date: '2026-05-16' },

  // ── May 17 ──────────────────────────────────────────────────────────────────
  { id: 119, name: 'Madison Square Garden',position: { lat: 40.7505, lng: -73.9934 }, type: 'sports',   borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Rangers – Conference Finals',      demandScore: 91, time: '19:00', date: '2026-05-17' },
  { id: 120, name: 'Yankee Stadium',       position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Athletics',             demandScore: 79, time: '13:05', date: '2026-05-17' },
  { id: 121, name: 'Citi Field',           position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Padres',                   demandScore: 70, time: '19:10', date: '2026-05-17' },
  { id: 122, name: 'Brooklyn Museum',      position: { lat: 40.6712, lng: -73.9636 }, type: 'festival', borough: 'Brooklyn',       neighbourhood: 'Park Slope',         eventName: 'First Saturday Night',             demandScore: 56, time: '17:00', date: '2026-05-17' },
  { id: 123, name: 'SI Yankees Stadium',   position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees Game',                  demandScore: 41, time: '18:00', date: '2026-05-17' },

  // ── May 19 ──────────────────────────────────────────────────────────────────
  { id: 124, name: 'Barclays Center',      position: { lat: 40.6826, lng: -73.9754 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'SZA – SOS Tour',                   demandScore: 93, time: '20:00', date: '2026-05-19' },
  { id: 125, name: 'Citi Field',           position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Giants',                   demandScore: 70, time: '19:10', date: '2026-05-19' },
  { id: 126, name: 'Yankee Stadium',       position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Red Sox',               demandScore: 86, time: '19:05', date: '2026-05-19' },
  { id: 127, name: 'Madison Square Garden',position: { lat: 40.7505, lng: -73.9934 }, type: 'sports',   borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Rangers – Conference Finals',      demandScore: 90, time: '20:00', date: '2026-05-19' },
  { id: 128, name: 'SI Yankees Stadium',   position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees Game',                  demandScore: 43, time: '18:00', date: '2026-05-19' },

  // ── May 20 ──────────────────────────────────────────────────────────────────
  { id: 129, name: 'Madison Square Garden',position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Taylor Swift – Eras Tour',         demandScore: 99, time: '19:00', date: '2026-05-20' },
  { id: 130, name: 'Prospect Park',        position: { lat: 40.6602, lng: -73.9690 }, type: 'festival', borough: 'Brooklyn',       neighbourhood: 'Park Slope',         eventName: 'Celebrate Brooklyn! Vol. 2',       demandScore: 60, time: '18:00', date: '2026-05-20' },
  { id: 131, name: 'Flushing Meadows Park',position: { lat: 40.7282, lng: -73.8456 }, type: 'festival', borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Asian American Heritage Fest',     demandScore: 53, time: '12:00', date: '2026-05-20' },
  { id: 132, name: 'Yankee Stadium',       position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Red Sox',               demandScore: 84, time: '19:05', date: '2026-05-20' },
  { id: 133, name: 'Snug Harbor',          position: { lat: 40.6437, lng: -74.1003 }, type: 'festival', borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'Memorial Day Spring Gala',         demandScore: 55, time: '14:00', date: '2026-05-20' },

  // ── May 21 ──────────────────────────────────────────────────────────────────
  { id: 134, name: 'Madison Square Garden',position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Taylor Swift – Night 2',           demandScore: 99, time: '19:00', date: '2026-05-21' },
  { id: 135, name: 'Yankee Stadium',       position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Marlins',               demandScore: 72, time: '19:05', date: '2026-05-21' },
  { id: 136, name: 'St. George Theatre',   position: { lat: 40.6436, lng: -74.0764 }, type: 'concert',  borough: 'Staten Island',  neighbourhood: 'St. George',         eventName: 'Indie Night – Local Acts',         demandScore: 33, time: '20:00', date: '2026-05-21' },
  { id: 137, name: 'Citi Field',           position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Marlins',                  demandScore: 68, time: '13:10', date: '2026-05-21' },
  { id: 138, name: 'Kings Theatre',        position: { lat: 40.6519, lng: -73.9495 }, type: 'concert',  borough: 'Brooklyn',       neighbourhood: 'Crown Heights',      eventName: 'Gospel Brunch & Live Music',       demandScore: 58, time: '11:00', date: '2026-05-21' },

  // ── May 22 ──────────────────────────────────────────────────────────────────
  { id: 139, name: 'Madison Square Garden',position: { lat: 40.7505, lng: -73.9934 }, type: 'concert',  borough: 'Manhattan',      neighbourhood: 'Midtown',            eventName: 'Taylor Swift – Night 3',           demandScore: 99, time: '19:00', date: '2026-05-22' },
  { id: 140, name: 'Barclays Center',      position: { lat: 40.6826, lng: -73.9754 }, type: 'sports',   borough: 'Brooklyn',       neighbourhood: 'Downtown Brooklyn',  eventName: 'Nets – Conference Finals',          demandScore: 92, time: '20:30', date: '2026-05-22' },
  { id: 141, name: 'Citi Field',           position: { lat: 40.7571, lng: -73.8458 }, type: 'sports',   borough: 'Queens',         neighbourhood: 'Flushing',           eventName: 'Mets vs Giants',                   demandScore: 68, time: '13:10', date: '2026-05-22' },
  { id: 142, name: 'Yankee Stadium',       position: { lat: 40.8296, lng: -73.9262 }, type: 'sports',   borough: 'Bronx',          neighbourhood: 'Fordham',           eventName: 'Yankees vs Marlins',               demandScore: 69, time: '13:05', date: '2026-05-22' },
  { id: 143, name: 'SI Yankees Stadium',   position: { lat: 40.6284, lng: -74.1502 }, type: 'sports',   borough: 'Staten Island',  neighbourhood: 'Stapleton',          eventName: 'SI Yankees Game',                  demandScore: 42, time: '18:00', date: '2026-05-22' },
];

export const BOROUGHS = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'];
export const EVENT_TYPES = ['concert', 'sports', 'festival'];

export const TYPE_COLORS = {
  concert:  'bg-purple-500',
  sports:   'bg-blue-500',
  festival: 'bg-green-500',
};

export const TYPE_TEXT_COLORS = {
  concert:  'text-purple-600',
  sports:   'text-blue-600',
  festival: 'text-green-600',
};

export const TYPE_BG_LIGHT = {
  concert:  'bg-purple-50',
  sports:   'bg-blue-50',
  festival: 'bg-green-50',
};
