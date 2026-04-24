import { useState, useRef } from 'react';
import { BrainCircuit, Globe, Camera, Wifi, Users, AlertTriangle, Search } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import UploadForm from '../components/UploadForm';

const FEATURES = [
  { icon: <BrainCircuit size={32} strokeWidth={1.5} color="var(--accent-cyan)" />, title: 'Face Intelligence', desc: 'RetinaFace + ArcFace 512D embeddings for military-grade face matching across any image source.' },
  { icon: <Globe size={32} strokeWidth={1.5} color="var(--accent-purple)" />, title: 'Multi-Source Crawl', desc: 'Instagram, Twitter, Facebook, Reddit, YouTube, Google Images, news — all searched simultaneously.' },
  { icon: <Camera size={32} strokeWidth={1.5} color="var(--accent-amber)" />, title: 'Camera Monitoring', desc: '900+ NYC DOT cameras + open IP cameras scanned every 10 minutes with expanding radius.' },
  { icon: <Wifi size={32} strokeWidth={1.5} color="var(--accent-green)" />, title: 'Expanding Search', desc: 'Auto-widens from 1mi → 5mi → 20mi → city → state. Resets on each confirmed match.' },
  { icon: <Users size={32} strokeWidth={1.5} color="var(--accent-cyan)" />, title: 'Crowdsourced Sightings', desc: 'Shareable link turns volunteers into live camera nodes. On-device detection, zero data transmitted.' },
  { icon: <AlertTriangle size={32} strokeWidth={1.5} color="var(--accent-red)" />, title: 'Instant Alerts', desc: 'Email, SMS, and push notifications the moment a high-confidence match is found.' },
];

export default function Landing() {
  const [showUpload, setShowUpload] = useState(false);
  const navigate = useNavigate();
  const uploadRef = useRef(null);

  const handlePersonCreated = (person) => {
    navigate(`/dashboard/${person.id}`);
  };

  const scrollToUpload = () => {
    setShowUpload(true);
    setTimeout(() => uploadRef.current?.scrollIntoView({ behavior: 'smooth' }), 100);
  };

  return (
    <div style={{ position: 'relative' }}>
      {/* Background effects */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
        background: 'radial-gradient(ellipse at 50% 0%, rgba(0,212,255,0.08) 0%, transparent 60%), radial-gradient(ellipse at 80% 100%, rgba(124,77,255,0.06) 0%, transparent 50%)',
      }} />

      {/* Hero Section */}
      <section style={{
        position: 'relative', zIndex: 1,
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        minHeight: 'calc(100vh - 64px)', textAlign: 'center', padding: '40px 24px',
      }}>
        {/* Eye animation */}
        <div className="animate-fade-in" style={{
          width: 120, height: 120, borderRadius: '50%', marginBottom: 32,
          background: 'radial-gradient(circle, rgba(0,212,255,0.15) 0%, transparent 70%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          animation: 'glow 3s ease-in-out infinite',
        }}>
          <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
            <ellipse cx="40" cy="40" rx="36" ry="24" stroke="url(#heroGrad)" strokeWidth="2.5" fill="none" opacity="0.8" />
            <circle cx="40" cy="40" r="14" fill="url(#heroGrad)" opacity="0.9" />
            <circle cx="40" cy="40" r="6" fill="#0a0e1a" />
            <circle cx="43" cy="37" r="2" fill="rgba(255,255,255,0.6)" />
            <defs>
              <linearGradient id="heroGrad" x1="0" y1="0" x2="80" y2="80">
                <stop stopColor="#00d4ff" />
                <stop offset="1" stopColor="#7c4dff" />
              </linearGradient>
            </defs>
          </svg>
        </div>

        <h1 className="animate-fade-in" style={{
          fontSize: 'clamp(2.5rem, 6vw, 4.5rem)', fontWeight: 900,
          letterSpacing: '-0.03em', marginBottom: 16, lineHeight: 1.1,
        }}>
          <span style={{
            background: 'linear-gradient(135deg, #f0f4ff, #00d4ff)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
          }}>Missing Person</span>
          <br />
          <span style={{
            background: 'linear-gradient(135deg, #00d4ff, #7c4dff)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
          }}>Intelligence System</span>
        </h1>

        <p className="animate-fade-in" style={{
          fontSize: '1.125rem', color: 'var(--text-secondary)',
          maxWidth: 600, marginBottom: 40, lineHeight: 1.7,
          animationDelay: '0.2s', animationFillMode: 'backwards',
        }}>
          Upload one photo. ThirdEye hunts your person across the entire open internet,
          public cameras, and crowdsourced sightings — <strong style={{ color: 'var(--accent-cyan)' }}>24/7</strong> — until they're found.
        </p>

        <div className="animate-fade-in" style={{
          display: 'flex', gap: 16, flexWrap: 'wrap', justifyContent: 'center',
          animationDelay: '0.4s', animationFillMode: 'backwards',
        }}>
          <button className="btn btn-primary" style={{ fontSize: '1rem', padding: '16px 36px' }} onClick={scrollToUpload}>
            <Search size={18} /> Start Search
          </button>
          <button className="btn btn-outline" style={{ fontSize: '1rem', padding: '16px 36px' }} onClick={() => {
            document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
          }}>
            Learn More
          </button>
        </div>

        {/* Stats ticker */}
        <div className="animate-fade-in" style={{
          display: 'flex', gap: 48, marginTop: 60, animationDelay: '0.6s', animationFillMode: 'backwards',
        }}>
          {[
            { val: '$0', label: 'Total Cost' },
            { val: '10+', label: 'Data Sources' },
            { val: '24/7', label: 'Always On' },
            { val: '900+', label: 'Public Cameras' },
          ].map((s, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>{s.val}</div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.1em' }}>{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" style={{ position: 'relative', zIndex: 1, padding: '80px 24px', maxWidth: 1200, margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', marginBottom: 12 }}>
          <span style={{
            background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
          }}>Core Capabilities</span>
        </h2>
        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', marginBottom: 48, maxWidth: 500, margin: '0 auto 48px' }}>
          Built for families, not law enforcement. Every feature is free and always will be.
        </p>

        <div className="grid grid-3">
          {FEATURES.map((f, i) => (
            <div key={i} className="glass-card" style={{ animationDelay: `${i * 0.1}s` }}>
              <div style={{ fontSize: '2rem', marginBottom: 12 }}>{f.icon}</div>
              <h4 style={{ marginBottom: 8, color: 'var(--text-primary)' }}>{f.title}</h4>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Upload Section */}
      {showUpload && (
        <section ref={uploadRef} style={{ position: 'relative', zIndex: 1, padding: '40px 24px 100px', maxWidth: 700, margin: '0 auto' }}>
          <UploadForm onPersonCreated={handlePersonCreated} />
        </section>
      )}

      {/* Footer */}
      <footer style={{
        textAlign: 'center', padding: '40px 24px',
        borderTop: '1px solid var(--border-subtle)',
        color: 'var(--text-muted)', fontSize: '0.8rem',
      }}>
        &copy; {new Date().getFullYear()} ThirdEye Intelligence System. All rights reserved.
      </footer>
    </div>
  );
}
