import { useNavigate, useLocation } from 'react-router-dom';

export default function NavButtons() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="absolute top-4 left-4 z-20 flex gap-2">
      <button
        onClick={() => navigate('/')}
        title="Map View"
        className={`w-11 h-11 rounded-full shadow-lg flex items-center justify-center transition-all ${
          location.pathname === '/'
            ? 'bg-blue-500 text-white'
            : 'bg-white text-gray-600 hover:bg-gray-50'
        }`}
      >
        {/* Map icon */}
        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/>
          <line x1="9" y1="3" x2="9" y2="18"/>
          <line x1="15" y1="6" x2="15" y2="21"/>
        </svg>
      </button>

      <button
        onClick={() => navigate('/list')}
        title="List View"
        className={`w-11 h-11 rounded-full shadow-lg flex items-center justify-center transition-all ${
          location.pathname === '/list'
            ? 'bg-blue-500 text-white'
            : 'bg-white text-gray-600 hover:bg-gray-50'
        }`}
      >
        {/* List icon */}
        <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="8" y1="6" x2="21" y2="6"/>
          <line x1="8" y1="12" x2="21" y2="12"/>
          <line x1="8" y1="18" x2="21" y2="18"/>
          <line x1="3" y1="6" x2="3.01" y2="6"/>
          <line x1="3" y1="12" x2="3.01" y2="12"/>
          <line x1="3" y1="18" x2="3.01" y2="18"/>
        </svg>
      </button>
    </div>
  );
}