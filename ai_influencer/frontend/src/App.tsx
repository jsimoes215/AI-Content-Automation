/**
 * AI Influencer Management POC - Frontend
 * React components for influencer management interface
 * 
 * Author: MiniMax Agent
 * Date: 2025-11-07
 */

import React, { useState, useEffect } from 'react';
import './App.css';

interface Influencer {
  id: number;
  name: string;
  bio: string;
  voice_type: string;
  personality_traits: string[];
  target_audience: any;
  branding_guidelines: any;
  is_active: boolean;
  created_at: string;
  niche_count: number;
}

interface Niche {
  id: number;
  name: string;
  description: string;
  target_keywords: string[];
  content_templates: any;
  tone_guidelines: any;
  performance_benchmarks: any;
  created_at: string;
}

interface AnalyticsSummary {
  active_influencers: number;
  total_niches: number;
  total_relationships: number;
  niche_distribution: Array<{
    name: string;
    influencer_count: number;
  }>;
  generated_at: string;
}

const API_BASE_URL = 'http://localhost:8000';

const App: React.FC = () => {
  const [influencers, setInfluencers] = useState<Influencer[]>([]);
  const [niches, setNiches] = useState<Niche[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'influencers' | 'niches' | 'analytics'>('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch data functions
  const fetchInfluencers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/influencers`);
      if (!response.ok) throw new Error('Failed to fetch influencers');
      const data = await response.json();
      setInfluencers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const fetchNiches = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/niches`);
      if (!response.ok) throw new Error('Failed to fetch niches');
      const data = await response.json();
      setNiches(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/analytics/summary`);
      if (!response.ok) throw new Error('Failed to fetch analytics');
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    }
  };

  useEffect(() => {
    fetchInfluencers();
    fetchNiches();
    fetchAnalytics();
  }, []);

  const handleCreateInfluencer = async (influencerData: Partial<Influencer>) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/influencers`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(influencerData),
      });
      if (!response.ok) throw new Error('Failed to create influencer');
      await fetchInfluencers();
      await fetchAnalytics();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create influencer');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteInfluencer = async (id: number) => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/influencers/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete influencer');
      await fetchInfluencers();
      await fetchAnalytics();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete influencer');
    } finally {
      setLoading(false);
    }
  };

  const getVoiceTypeDisplay = (voiceType: string) => {
    const displayNames: { [key: string]: string } = {
      'professional_male': 'Professional Male',
      'professional_female': 'Professional Female',
      'energetic_male': 'Energetic Male',
      'energetic_female': 'Energetic Female',
      'casual_male': 'Casual Male',
      'casual_female': 'Casual Female'
    };
    return displayNames[voiceType] || voiceType;
  };

  // Tab Components
  const OverviewTab = () => (
    <div className="overview-tab">
      <h2>AI Influencer Management System</h2>
      {analytics && (
        <div className="analytics-grid">
          <div className="metric-card">
            <h3>{analytics.active_influencers}</h3>
            <p>Active Influencers</p>
          </div>
          <div className="metric-card">
            <h3>{analytics.total_niches}</h3>
            <p>Available Niches</p>
          </div>
          <div className="metric-card">
            <h3>{analytics.total_relationships}</h3>
            <p>Influencer-Niche Links</p>
          </div>
        </div>
      )}
      
      <div className="quick-actions">
        <h3>Quick Actions</h3>
        <div className="action-buttons">
          <button 
            onClick={() => setActiveTab('influencers')}
            className="btn btn-primary"
          >
            Manage Influencers
          </button>
          <button 
            onClick={() => setActiveTab('niches')}
            className="btn btn-secondary"
          >
            Browse Niches
          </button>
          <button 
            onClick={() => setActiveTab('analytics')}
            className="btn btn-info"
          >
            View Analytics
          </button>
        </div>
      </div>

      {analytics && analytics.niche_distribution.length > 0 && (
        <div className="niche-distribution">
          <h3>Influencer Distribution by Niche</h3>
          <div className="distribution-list">
            {analytics.niche_distribution.map((niche) => (
              <div key={niche.name} className="distribution-item">
                <span className="niche-name">{niche.name.replace('_', ' ')}</span>
                <span className="influencer-count">{niche.influencer_count} influencers</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  const InfluencersTab = () => (
    <div className="influencers-tab">
      <div className="tab-header">
        <h2>Influencer Management</h2>
        <button 
          onClick={() => setActiveTab('create-influencer')}
          className="btn btn-primary"
        >
          Create New Influencer
        </button>
      </div>

      {loading && <div className="loading">Loading influencers...</div>}
      {error && <div className="error">{error}</div>}

      <div className="influencers-grid">
        {influencers.map((influencer) => (
          <div key={influencer.id} className="influencer-card">
            <div className="influencer-header">
              <h3>{influencer.name}</h3>
              <div className="influencer-actions">
                <button 
                  onClick={() => handleDeleteInfluencer(influencer.id)}
                  className="btn btn-danger btn-sm"
                  disabled={loading}
                >
                  Delete
                </button>
              </div>
            </div>
            
            <div className="influencer-content">
              <p className="bio">{influencer.bio}</p>
              
              <div className="influencer-meta">
                <div className="meta-item">
                  <strong>Voice Type:</strong> {getVoiceTypeDisplay(influencer.voice_type)}
                </div>
                <div className="meta-item">
                  <strong>Active Niches:</strong> {influencer.niche_count}
                </div>
                <div className="meta-item">
                  <strong>Personality Traits:</strong>
                  <div className="traits-list">
                    {influencer.personality_traits.map((trait, index) => (
                      <span key={index} className="trait-tag">{trait}</span>
                    ))}
                  </div>
                </div>
                <div className="meta-item">
                  <strong>Status:</strong> 
                  <span className={`status ${influencer.is_active ? 'active' : 'inactive'}`}>
                    {influencer.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {influencers.length === 0 && !loading && (
        <div className="empty-state">
          <h3>No influencers found</h3>
          <p>Create your first AI influencer to get started!</p>
          <button 
            onClick={() => setActiveTab('create-influencer')}
            className="btn btn-primary"
          >
            Create Influencer
          </button>
        </div>
      )}
    </div>
  );

  const NichesTab = () => (
    <div className="niches-tab">
      <h2>Available Niches</h2>
      
      {loading && <div className="loading">Loading niches...</div>}
      
      <div className="niches-grid">
        {niches.map((niche) => (
          <div key={niche.id} className="niche-card">
            <div className="niche-header">
              <h3>{niche.name.replace('_', ' ')}</h3>
            </div>
            
            <div className="niche-content">
              <p className="description">{niche.description}</p>
              
              <div className="niche-meta">
                <div className="keywords-section">
                  <strong>Target Keywords:</strong>
                  <div className="keywords-list">
                    {niche.target_keywords.map((keyword, index) => (
                      <span key={index} className="keyword-tag">{keyword}</span>
                    ))}
                  </div>
                </div>
                
                {niche.tone_guidelines && Object.keys(niche.tone_guidelines).length > 0 && (
                  <div className="tone-section">
                    <strong>Tone Guidelines:</strong>
                    <div className="tone-list">
                      {Object.entries(niche.tone_guidelines).map(([key, value]) => (
                        <div key={key} className="tone-item">
                          <span className="tone-key">{key.replace('_', ' ')}:</span>
                          <span className="tone-value">{value as string}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const AnalyticsTab = () => (
    <div className="analytics-tab">
      <h2>System Analytics</h2>
      
      {analytics && (
        <>
          <div className="analytics-overview">
            <div className="metric-cards">
              <div className="metric-card">
                <h3>{analytics.active_influencers}</h3>
                <p>Active Influencers</p>
              </div>
              <div className="metric-card">
                <h3>{analytics.total_niches}</h3>
                <p>Total Niches</p>
              </div>
              <div className="metric-card">
                <h3>{analytics.total_relationships}</h3>
                <p>Influencer-Niche Relationships</p>
              </div>
            </div>
            
            <div className="last-updated">
              <p>Last updated: {new Date(analytics.generated_at).toLocaleString()}</p>
            </div>
          </div>
          
          {analytics.niche_distribution.length > 0 && (
            <div className="niche-analytics">
              <h3>Influencer Distribution by Niche</h3>
              <div className="distribution-chart">
                {analytics.niche_distribution.map((niche) => (
                  <div key={niche.name} className="distribution-bar">
                    <div className="bar-label">{niche.name.replace('_', ' ')}</div>
                    <div className="bar-container">
                      <div 
                        className="bar-fill" 
                        style={{ 
                          width: `${Math.max((niche.influencer_count / Math.max(...analytics.niche_distribution.map(n => n.influencer_count))) * 100, 10)}%` 
                        }}
                      ></div>
                    </div>
                    <div className="bar-value">{niche.influencer_count}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Influencer Management System</h1>
        <p>Manage AI-powered influencers across multiple niches</p>
      </header>
      
      <nav className="navigation">
        <button 
          className={`nav-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button 
          className={`nav-button ${activeTab === 'influencers' ? 'active' : ''}`}
          onClick={() => setActiveTab('influencers')}
        >
          Influencers
        </button>
        <button 
          className={`nav-button ${activeTab === 'niches' ? 'active' : ''}`}
          onClick={() => setActiveTab('niches')}
        >
          Niches
        </button>
        <button 
          className={`nav-button ${activeTab === 'analytics' ? 'active' : ''}`}
          onClick={() => setActiveTab('analytics')}
        >
          Analytics
        </button>
      </nav>
      
      <main className="main-content">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'influencers' && <InfluencersTab />}
        {activeTab === 'niches' && <NichesTab />}
        {activeTab === 'analytics' && <AnalyticsTab />}
      </main>
      
      <footer className="app-footer">
        <p>AI Influencer Management POC - Built with React & FastAPI</p>
        <p>Author: MiniMax Agent | Date: 2025-11-07</p>
      </footer>
    </div>
  );
};

export default App;