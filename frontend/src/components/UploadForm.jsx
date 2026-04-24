import { useState, useRef } from 'react';
import { Camera, Eye } from 'lucide-react';
import { api } from '../utils/api';

export default function UploadForm({ onPersonCreated }) {
  const [files, setFiles] = useState([]);
  const [previews, setPreviews] = useState([]);
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [description, setDescription] = useState('');
  const [lastLocation, setLastLocation] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  const handleFiles = (newFiles) => {
    const imageFiles = Array.from(newFiles).filter(f => f.type.startsWith('image/'));
    setFiles(prev => [...prev, ...imageFiles]);
    imageFiles.forEach(f => {
      const reader = new FileReader();
      reader.onload = (e) => setPreviews(prev => [...prev, e.target.result]);
      reader.readAsDataURL(f);
    });
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    handleFiles(e.dataTransfer.files);
  };

  const removeFile = (idx) => {
    setFiles(prev => prev.filter((_, i) => i !== idx));
    setPreviews(prev => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (files.length === 0) { setError('Please upload at least one photo'); return; }
    setLoading(true);
    setError('');

    try {
      const formData = new FormData();
      files.forEach(f => formData.append('photos', f));
      if (name) formData.append('name', name);
      if (age) formData.append('age', age);
      if (gender) formData.append('gender', gender);
      if (description) formData.append('description', description);
      if (lastLocation) formData.append('last_known_location', lastLocation);

      const person = await api.createPerson(formData);
      onPersonCreated(person);
    } catch (err) {
      setError(err.message || 'Failed to create search profile');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="glass-card" style={{ padding: 32 }}>
      <h3 style={{ marginBottom: 4 }}>
        <span style={{
          background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-purple))',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text',
        }}>Start a Search</span>
      </h3>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 24 }}>
        Upload one or more photos of the missing person. More photos = better accuracy.
      </p>

      {/* Drop zone */}
      <div
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
        onDragLeave={() => setDragActive(false)}
        onDrop={handleDrop}
        style={{
          border: `2px dashed ${dragActive ? 'var(--accent-cyan)' : 'var(--border-medium)'}`,
          borderRadius: 'var(--radius-lg)',
          padding: '40px 24px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all var(--transition-normal)',
          background: dragActive ? 'var(--accent-cyan-glow)' : 'transparent',
          marginBottom: 20,
        }}
      >
        <input ref={inputRef} type="file" accept="image/*" multiple onChange={e => handleFiles(e.target.files)} style={{ display: 'none' }} />
        <div style={{ marginBottom: 8 }}><Camera size={40} color="var(--text-muted)" /></div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          <strong style={{ color: 'var(--accent-cyan)' }}>Click to upload</strong> or drag and drop
        </p>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginTop: 4 }}>JPG, PNG — multiple photos recommended</p>
      </div>

      {/* Previews */}
      {previews.length > 0 && (
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
          {previews.map((src, i) => (
            <div key={i} style={{ position: 'relative', width: 80, height: 80, borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '2px solid var(--border-accent)' }}>
              <img src={src} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
              <button type="button" onClick={() => removeFile(i)} style={{
                position: 'absolute', top: -6, right: -6, width: 20, height: 20,
                borderRadius: '50%', background: 'var(--accent-red)', border: 'none',
                color: 'white', fontSize: '0.65rem', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>✕</button>
            </div>
          ))}
        </div>
      )}

      {/* Optional Details */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <div>
          <label className="input-label">Name (optional)</label>
          <input className="input" placeholder="Full name" value={name} onChange={e => setName(e.target.value)} />
        </div>
        <div>
          <label className="input-label">Age (optional)</label>
          <input className="input" type="number" placeholder="Age" value={age} onChange={e => setAge(e.target.value)} />
        </div>
        <div>
          <label className="input-label">Gender (optional)</label>
          <select className="input" value={gender} onChange={e => setGender(e.target.value)}>
            <option value="">Select...</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label className="input-label">Last Known Location</label>
          <input className="input" placeholder="City, State" value={lastLocation} onChange={e => setLastLocation(e.target.value)} />
        </div>
      </div>

      <div style={{ marginBottom: 24 }}>
        <label className="input-label">Description (optional)</label>
        <textarea className="input" rows={3} placeholder="Any identifying details..." value={description} onChange={e => setDescription(e.target.value)} style={{ resize: 'vertical' }} />
      </div>

      {error && <p style={{ color: 'var(--accent-red)', fontSize: '0.875rem', marginBottom: 16 }}>⚠️ {error}</p>}

      <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: '100%', padding: '16px', fontSize: '1rem' }}>
        {loading ? (
          <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ width: 18, height: 18, border: '2px solid transparent', borderTopColor: 'var(--bg-primary)', borderRadius: '50%', animation: 'rotate 0.8s linear infinite', display: 'inline-block' }} />
            Processing...
          </span>
        ) : <><Eye size={18} /> Begin Search</>}
      </button>
    </form>
  );
}
