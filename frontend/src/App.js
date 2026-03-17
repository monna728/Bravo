import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MapPage from './pages/MapPage';
import ListPage from './pages/ListPage';
import LandingPage from './pages/LandingPage';
import NavButtons from './components/NavButtons';

function App() {
  return (
    <BrowserRouter>
      <div className="w-screen h-screen">
        <NavButtons />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/map" element={<MapPage />} />
          <Route path="/list" element={<ListPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;