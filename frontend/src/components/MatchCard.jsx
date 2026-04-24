import { API_URL } from '../utils/api';
import { MapPin, MessageSquare, Clock, Camera, MessageCircle, Hash, Bot, Tv, Search, RefreshCw, Newspaper, Video, Globe, Users, TextSearch, MapPin as Pin } from 'lucide-react';

function getConfidenceClass(label) {
  if (!label) return 'possible';
  const l = label.toLowerCase();
  if (l.includes('definite')) return 'definite';
  if (l.includes('high')) return 'high';
  if (l.includes('probable')) return 'probable';
  return 'possible';
}

function getSourceIcon(source) {
  const map = {
    instagram: <Camera size={20} />, twitter: <Hash size={20} />, facebook: <MessageCircle size={20} />, reddit: <Bot size={20} />,
    youtube: <Tv size={20} />, google_images: <Search size={20} />, google_reverse_image: <RefreshCw size={20} />,
    news: <Newspaper size={20} />, nyc_dot_cam: <Video size={20} />, shodan_cam: <Globe size={20} />,
    crowdsource: <Users size={20} />, username: <TextSearch size={20} />,
  };
  for (const [key, icon] of Object.entries(map)) {
    if (source?.includes(key)) return icon;
  }
  return <Pin size={20} />;
}

export default function MatchCard({ match, personPhotos = [], index = 0 }) {
  const cls = getConfidenceClass(match.confidence_label);
  const pct = Math.round((match.similarity || 0) * 100);
  const refPhoto = personPhotos[0] ? `${API_URL}${personPhotos[0]}` : null;

  return (
    <div className="glass-card animate-slide-in" style={{
      animationDelay: `${index * 0.05}s`, animationFillMode: 'backwards',
      display: 'flex', flexDirection: 'column', gap: 16, padding: 20,
    }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ display: 'flex', alignItems: 'center' }}>{getSourceIcon(match.source)}</span>
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)', textTransform: 'capitalize' }}>
            {match.source?.replace(/_/g, ' ')}
          </span>
        </div>
        <span className={`badge badge-${cls}`}>{match.confidence_label}</span>
      </div>

      {/* Images side by side */}
      <div style={{ display: 'flex', gap: 12 }}>
        {refPhoto && (
          <div style={{ flex: 1, position: 'relative' }}>
            <div style={{ fontSize: '0.6rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Reference</div>
            <div style={{ width: '100%', aspectRatio: '1', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-subtle)' }}>
              <img src={refPhoto} alt="Reference" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => e.target.style.display = 'none'} />
            </div>
          </div>
        )}
        {match.image_url && (
          <div style={{ flex: 1, position: 'relative' }}>
            <div style={{ fontSize: '0.6rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 4 }}>Match</div>
            <div style={{ width: '100%', aspectRatio: '1', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: `1px solid ${cls === 'definite' ? 'var(--accent-red)' : 'var(--border-subtle)'}` }}>
              <img src={match.image_url} alt="Match" style={{ width: '100%', height: '100%', objectFit: 'cover' }} onError={e => e.target.style.display = 'none'} />
            </div>
          </div>
        )}
      </div>

      {/* Confidence Bar */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
          <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Confidence</span>
          <span style={{ fontSize: '0.8rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: `var(--accent-${cls === 'definite' ? 'red' : cls === 'high' ? 'amber' : cls === 'probable' ? 'purple' : 'cyan'})` }}>
            {pct}%
          </span>
        </div>
        <div className="confidence-bar">
          <div className={`confidence-bar-fill ${cls}`} style={{ width: `${pct}%` }} />
        </div>
      </div>

      {/* Details */}
      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: 4 }}>
        {match.location && <div style={{display: 'flex', alignItems: 'center', gap: 4}}><MapPin size={14} /> {match.location}</div>}
        {match.raw_text && <div style={{ display: 'flex', alignItems: 'center', gap: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '100%' }}><MessageSquare size={14} style={{flexShrink: 0}} /> {match.raw_text.slice(0, 80)}</div>}
        {match.created_at && <div style={{ color: 'var(--text-muted)', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: 4 }}><Clock size={12} /> {new Date(match.created_at).toLocaleString()}</div>}
      </div>

      {/* Actions */}
      {match.url && (
        <a href={match.url} target="_blank" rel="noopener noreferrer" className="btn btn-outline" style={{ fontSize: '0.75rem', padding: '8px 16px' }}>
          View Source →
        </a>
      )}
    </div>
  );
}
