import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../utils/api';
import { useWebSocket } from '../hooks/useWebSocket';
import StatsPanel from '../components/StatsPanel';
import MatchCard from '../components/MatchCard';
import MapView from '../components/MapView';
import Timeline from '../components/Timeline';
import ShareLink from '../components/ShareLink';
import { Target, Map as MapIcon, Clock, Users, Zap, Search } from 'lucide-react';

export default function Dashboard() {
  const { personId } = useParams();
  const [person, setPerson] = useState(null);
  const [matches, setMatches] = useState([]);
  const [stats, setStats] = useState(null);
  const [mapData, setMapData] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [activeTab, setActiveTab] = useState('matches');
  const [loading, setLoading] = useState(true);
  const { isConnected, lastEvent } = useWebSocket(personId);

  useEffect(() => {
    loadData();
  }, [personId]);

  useEffect(() => {
    if (lastEvent?.event === 'new_match' || lastEvent?.event === 'scan_complete') {
      loadData();
    }
  }, [lastEvent]);

  const loadData = async () => {
    try {
      const [p, m, s, md, t] = await Promise.all([
        api.getPerson(personId),
        api.getMatches(personId),
        api.getStats(personId).catch(() => null),
        api.getMapData(personId).catch(() => null),
        api.getTimeline(personId).catch(() => ({ timeline: [] })),
      ]);
      setPerson(p);
      setMatches(m.matches || []);
      setStats(s);
      setMapData(md);
      setTimeline(t.timeline || []);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = async () => {
    try {
      await api.triggerScan(personId);
    } catch (err) {
      console.error('Scan trigger failed:', err);
    }
  };

  if (loading) {
    return (
      <div className="page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: 48, height: 48, border: '3px solid var(--border-subtle)', borderTopColor: 'var(--accent-cyan)', borderRadius: '50%', animation: 'rotate 0.8s linear infinite', margin: '0 auto 16px' }} />
          <p style={{ color: 'var(--text-secondary)' }}>Loading intelligence dashboard...</p>
        </div>
      </div>
    );
  }

  if (!person) {
    return (
      <div className="page" style={{ textAlign: 'center', paddingTop: 80 }}>
        <h2>Person not found</h2>
        <p style={{ color: 'var(--text-secondary)' }}>The search profile doesn't exist or has been removed.</p>
      </div>
    );
  }

  const TABS = [
    { key: 'matches', label: <div style={{display: 'flex', alignItems: 'center', gap: 6}}><Target size={16} /> Matches</div>, count: matches.length },
    { key: 'map', label: <div style={{display: 'flex', alignItems: 'center', gap: 6}}><MapIcon size={16} /> Map</div> },
    { key: 'timeline', label: <div style={{display: 'flex', alignItems: 'center', gap: 6}}><Clock size={16} /> Timeline</div> },
    { key: 'share', label: <div style={{display: 'flex', alignItems: 'center', gap: 6}}><Users size={16} /> Crowdsource</div> },
  ];

  return (
    <div className="page">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
            <h2 style={{ margin: 0 }}>{person.name || 'Unknown Person'}</h2>
            <span className={`badge badge-${person.status === 'active' ? 'active' : 'possible'}`}>
              {person.status}
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
            {person.last_known_location && `Last seen: ${person.last_known_location} · `}
            ID: <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>{personId.slice(0, 8)}</code>
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div className={`live-indicator`} style={{ color: isConnected ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            <span className="live-dot" style={{ background: isConnected ? 'var(--accent-green)' : 'var(--accent-red)' }} />
            {isConnected ? 'Connected' : 'Reconnecting...'}
          </div>
          <button className="btn btn-primary" onClick={handleScan}><Zap size={18} /> Scan Now</button>
        </div>
      </div>

      {/* Stats */}
      <StatsPanel stats={stats} person={person} />

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid var(--border-subtle)', paddingBottom: 0 }}>
        {TABS.map(tab => (
          <button key={tab.key} className="btn btn-ghost" onClick={() => setActiveTab(tab.key)} style={{
            borderBottom: activeTab === tab.key ? '2px solid var(--accent-cyan)' : '2px solid transparent',
            borderRadius: 0, color: activeTab === tab.key ? 'var(--accent-cyan)' : 'var(--text-secondary)',
            paddingBottom: 12,
          }}>
            {tab.label}
            {tab.count !== undefined && <span style={{
              marginLeft: 6, fontSize: '0.7rem', background: 'var(--accent-cyan-glow)',
              color: 'var(--accent-cyan)', padding: '2px 8px', borderRadius: 'var(--radius-full)',
            }}>{tab.count}</span>}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'matches' && (
        <div className="animate-fade-in">
          {matches.length === 0 ? (
            <div className="glass-card" style={{ textAlign: 'center', padding: 48 }}>
              <div style={{ marginBottom: 12, opacity: 0.5, display: 'flex', justifyContent: 'center' }}><Search size={48} /></div>
              <h4 style={{ marginBottom: 8 }}>No matches yet</h4>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                The system is actively scanning. Matches will appear here as they're found.
              </p>
            </div>
          ) : (
            <div className="grid grid-2">
              {matches.map((match, i) => (
                <MatchCard key={match.id || i} match={match} personPhotos={person.photos} index={i} />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'map' && (
        <div className="animate-fade-in">
          <MapView mapData={mapData} person={person} />
        </div>
      )}

      {activeTab === 'timeline' && (
        <div className="animate-fade-in">
          <Timeline timeline={timeline} />
        </div>
      )}

      {activeTab === 'share' && (
        <div className="animate-fade-in">
          <ShareLink person={person} />
        </div>
      )}
    </div>
  );
}
