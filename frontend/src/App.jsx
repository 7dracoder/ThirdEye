import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import './index.css';

function Navbar() {
  return (
    <nav className="navbar">
      <a href="/" className="navbar-brand">
        <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
          <circle cx="14" cy="14" r="12" stroke="url(#grad)" strokeWidth="2" fill="none" />
          <circle cx="14" cy="14" r="6" fill="url(#grad)" />
          <circle cx="14" cy="14" r="2.5" fill="#0a0e1a" />
          <defs>
            <linearGradient id="grad" x1="0" y1="0" x2="28" y2="28">
              <stop stopColor="#00d4ff" />
              <stop offset="1" stopColor="#7c4dff" />
            </linearGradient>
          </defs>
        </svg>
        <span>ThirdEye</span>
      </a>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div className="live-indicator">
          <span className="live-dot"></span>
          System Active
        </div>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard/:personId" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
