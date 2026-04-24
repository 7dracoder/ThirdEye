import { Activity, Pause } from 'lucide-react';

export default function StatsPanel({ stats, person }) {
  const cards = [
    {
      label: 'Status',
      value: person?.status === 'active' ? <div style={{display: 'flex', alignItems: 'center', gap: 8}}><Activity size={20} /> ACTIVE</div> : <div style={{display: 'flex', alignItems: 'center', gap: 8}}><Pause size={20} /> Paused</div>,
      color: 'var(--accent-green)',
    },
    {
      label: 'Total Matches',
      value: stats?.total_matches ?? 0,
      color: 'var(--accent-cyan)',
    },
    {
      label: 'High Confidence',
      value: stats?.high_confidence_matches ?? 0,
      color: 'var(--accent-red)',
      subtitle: '≥ 75% confidence'
    },
    {
      label: 'Sources Active',
      value: stats?.sources_checked ?? 0,
      color: 'var(--accent-purple)',
    },
    {
      label: 'Search Radius',
      value: `${person?.current_radius ?? 1} mi`,
      color: 'var(--accent-amber)',
    },
    {
      label: 'Running Time',
      value: stats?.time_running_hours
        ? stats.time_running_hours < 1
          ? `${Math.round(stats.time_running_hours * 60)}m`
          : `${stats.time_running_hours.toFixed(1)}h`
        : '0m',
      color: 'var(--text-secondary)',
    },
  ];

  return (
    <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', marginBottom: 24 }}>
      {cards.map((card, i) => (
        <div key={i} className="glass-card" style={{
          padding: '16px 20px',
          display: 'flex', flexDirection: 'column', gap: 4,
        }}>
          <span style={{
            fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase',
            letterSpacing: '0.08em', color: 'var(--text-muted)',
          }}>
            {card.label}
          </span>
          <span style={{
            fontSize: '1.5rem', fontWeight: 800, color: card.color,
            fontFamily: 'var(--font-mono)',
          }}>
            {card.value}
          </span>
          {card.subtitle && (
            <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{card.subtitle}</span>
          )}
        </div>
      ))}
    </div>
  );
}
