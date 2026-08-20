import { Link } from 'react-router-dom';
import GalaxyBackground from '../components/GalaxyBackground';

const FLOW_STEPS = ['Event', 'Intelligence', 'Opportunity', 'Action', 'Outcome', 'Performance'];

export default function LandingPage() {
  return (
    <div className="landing-page">
      <GalaxyBackground />

      <nav className="landing-nav">
        <div className="landing-nav-brand">
          <div className="sidebar-brand-icon">M</div>
          Matkayena
        </div>
        <Link to="/login" className="btn btn-primary">Sign In</Link>
      </nav>

      <div className="landing-hero">
        <div className="landing-badge">Event-Driven Sales Intelligence</div>

        <h1 className="landing-title">
          Turn Customer Events into <span>Actionable Revenue</span>
        </h1>

        <p className="landing-subtitle">
          Deterministic intelligence transforms deposits, digital activity, and customer signals
          into prioritized opportunities with full explainability — no black boxes.
        </p>

        <div className="landing-cta">
          <Link to="/login" className="btn btn-primary btn-lg">Get Started</Link>
          <a href="#flow" className="btn btn-secondary btn-lg">How It Works</a>
        </div>

        <div className="landing-flow" id="flow">
          {FLOW_STEPS.map((step, i) => (
            <span key={step} style={{ display: 'inline-flex', alignItems: 'center', gap: '12px' }}>
              <span className="flow-step">{step}</span>
              {i < FLOW_STEPS.length - 1 && <span className="flow-arrow">→</span>}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
