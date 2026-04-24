import { Clock, MapPin, Radio } from 'lucide-react';

export default function Timeline({ timeline }) {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="glass-card" style={{ textAlign: 'center', padding: 48 }}>
        <div style={{ marginBottom: 12, opacity: 0.5, display: 'flex', justifyContent: 'center' }}><Clock size={48} /></div>
        <h4 style={{ marginBottom: 8 }}>No timeline data yet</h4>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
          Location points will appear here as matches are confirmed with GPS data.
        </p>
      </div>
    );
  }

  return (
    <div className="glass-card" style={{ padding: 24 }}>
      <h4 style={{ marginBottom: 24 }}>Movement Timeline</h4>

      <div style={{ position: 'relative', paddingLeft: 32 }}>
        {/* Vertical line */}
        <div style={{
          position: 'absolute', left: 7, top: 8, bottom: 8, width: 2,
          background: 'linear-gradient(180deg, var(--accent-cyan), var(--accent-purple))',
          borderRadius: 1,
        }} />

        {timeline.map((entry, i) => {
          const isFirst = i === 0;
          const isLast = i === timeline.length - 1;
          const time = entry.timestamp ? new Date(entry.timestamp) : null;

          return (
            <div key={entry.id || i} className="animate-fade-in" style={{
              position: 'relative', paddingBottom: isLast ? 0 : 28,
              animationDelay: `${i * 0.05}s`, animationFillMode: 'backwards',
            }}>
              {/* Dot */}
              <div style={{
                position: 'absolute', left: -28, top: 4,
                width: 14, height: 14, borderRadius: '50%',
                background: isFirst ? 'var(--accent-cyan)' : isLast ? 'var(--accent-purple)' : 'var(--bg-elevated)',
                border: `2px solid ${isFirst ? 'var(--accent-cyan)' : isLast ? 'var(--accent-purple)' : 'var(--text-muted)'}`,
                boxShadow: isFirst ? '0 0 8px rgba(0,212,255,0.5)' : 'none',
              }} />

              <div style={{
                background: 'var(--bg-card)', borderRadius: 'var(--radius-md)',
                padding: '12px 16px', border: '1px solid var(--border-subtle)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                  <span style={{ fontWeight: 600, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: 6 }}><MapPin size={16} /> {entry.location}</span>
                  {entry.confidence && (
                    <span className="badge badge-possible" style={{ fontSize: '0.6rem' }}>
                      {Math.round(entry.confidence * 100)}%
                    </span>
                  )}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', gap: 16 }}>
                  {time && <span style={{display: 'flex', alignItems: 'center', gap: 4}}><Clock size={12} /> {time.toLocaleString()}</span>}
                  {entry.source && <span style={{display: 'flex', alignItems: 'center', gap: 4}}><Radio size={12} /> {entry.source}</span>}
                  {entry.lat && entry.lng && (
                    <span style={{ fontFamily: 'var(--font-mono)' }}>
                      {entry.lat.toFixed(4)}, {entry.lng.toFixed(4)}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
