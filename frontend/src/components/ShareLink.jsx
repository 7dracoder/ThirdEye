import { useState } from 'react';
import { Copy, Check, Smartphone, Link, Camera, BrainCircuit, AlertTriangle, ShieldCheck } from 'lucide-react';

export default function ShareLink({ person }) {
  const [copied, setCopied] = useState(false);

  const shareUrl = `${window.location.origin}/sighting/${person.share_token}`;

  const copyLink = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      {/* Share Link Card */}
      <div className="glass-card" style={{ padding: 32 }}>
        <h4 style={{ marginBottom: 8 }}>
          <span style={{
            background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
          }}>Crowdsource Sightings</span>
        </h4>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 24 }}>
          Share this link with volunteers. Anyone with the link can submit a photo sighting
          that will be automatically face-matched against the reference photos.
        </p>

        {/* URL display */}
        <div style={{
          display: 'flex', gap: 8, marginBottom: 24,
        }}>
          <div style={{
            flex: 1, padding: '12px 16px',
            background: 'var(--bg-input)', borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
            fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-secondary)',
            overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }}>
            {shareUrl}
          </div>
          <button className="btn btn-primary" onClick={copyLink} style={{ whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: 6 }}>
            {copied ? <><Check size={16} /> Copied!</> : <><Copy size={16} /> Copy Link</>}
          </button>
        </div>

        {/* QR placeholder */}
        <div style={{
          width: 180, height: 180, margin: '0 auto',
          background: 'white', borderRadius: 'var(--radius-md)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          padding: 16,
        }}>
          <div style={{ textAlign: 'center', color: '#333' }}>
            <div style={{ marginBottom: 8, display: 'flex', justifyContent: 'center' }}><Smartphone size={48} color="#333" /></div>
            <div style={{ fontSize: '0.7rem', fontWeight: 600 }}>QR Code</div>
            <div style={{ fontSize: '0.6rem', color: '#666' }}>Scan to submit sighting</div>
          </div>
        </div>
      </div>

      {/* How it works */}
      <div className="glass-card" style={{ padding: 32 }}>
        <h4 style={{ marginBottom: 16 }}>How It Works</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 20 }}>
          {[
            { step: '1', icon: <Link size={24} color="var(--accent-cyan)" />, title: 'Share the Link', desc: 'Send the link to volunteers, community groups, or post on social media.' },
            { step: '2', icon: <Camera size={24} color="var(--accent-cyan)" />, title: 'Submit Photo', desc: 'Volunteer opens link, takes or uploads a photo of the potential sighting.' },
            { step: '3', icon: <BrainCircuit size={24} color="var(--accent-cyan)" />, title: 'Auto Face-Match', desc: 'The system automatically compares the submission against reference photos.' },
            { step: '4', icon: <AlertTriangle size={24} color="var(--accent-cyan)" />, title: 'Instant Alert', desc: 'If confidence ≥ 75%, you receive an immediate alert with location data.' },
          ].map((item, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{
                width: 48, height: 48, borderRadius: '50%', margin: '0 auto 12px',
                background: 'var(--accent-cyan-glow)', border: '1px solid var(--border-accent)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: '1.5rem',
              }}>
                {item.icon}
              </div>
              <h4 style={{ fontSize: '0.9rem', marginBottom: 4 }}>{item.title}</h4>
              <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>{item.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Privacy */}
      <div className="glass-card" style={{ padding: 20, border: '1px solid rgba(0, 230, 118, 0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center' }}><ShieldCheck size={24} color="var(--accent-green)" /></div>
          <div>
            <h4 style={{ fontSize: '0.9rem', marginBottom: 2, color: 'var(--accent-green)' }}>Privacy Guarantee</h4>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', margin: 0 }}>
              In live camera mode, no video ever leaves the volunteer's device. Only a boolean match result
              + GPS coordinates are transmitted on a positive match. No volunteer data is stored beyond the match event.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
