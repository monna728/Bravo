import { useNavigate } from 'react-router-dom';

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="w-screen h-screen bg-gray-900 flex flex-col items-center justify-center relative overflow-hidden">

      {/* Background grid */}
      <div className="absolute inset-0 opacity-10"
        style={{
          backgroundImage: 'linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px)',
          backgroundSize: '60px 60px',
        }}
      />

      {/* Glow */}
      <div className="absolute w-96 h-96 bg-blue-500 rounded-full opacity-10 blur-3xl" />

      {/* Content */}
      <div className="relative z-10 text-center px-6">
        <h1 className="text-7xl font-black text-white tracking-tight mb-4">
          rush<span className="text-blue-400">hour</span>
        </h1>
        <p className="text-gray-400 text-xl mb-10 font-light">
          Find your crowd.
        </p>
        <button
          onClick={() => navigate('/map')}
          className="px-8 py-3 bg-blue-500 hover:bg-blue-400 text-white font-semibold rounded-full text-base shadow-lg shadow-blue-500/30 transition-all hover:scale-105 hover:shadow-blue-400/40"
        >
          Start Exploring →
        </button>
      </div>

      {/* Bottom label */}
      <p className="absolute bottom-6 text-gray-600 text-xs tracking-widest uppercase">
        NYC Taxi Demand Intelligence
      </p>
    </div>
  );
}