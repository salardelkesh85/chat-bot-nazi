import { useEffect, useState } from "react";
import { Heart, Brain, MessageCircle, Plus, ShieldCheck, Sparkles } from "lucide-react";

type Health = {
  status: string;
  database: string;
  mode: string;
};

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((response) => {
        if (!response.ok) throw new Error("Backend unavailable");
        return response.json();
      })
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <main className="shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark"><Heart size={19} fill="currentColor" /></span><span>NAZI <b>AI</b></span></div>
        <div className="side-label">WORKSPACE</div>
        <button className="nav-item active"><MessageCircle size={17} /> Conversations</button>
        <button className="nav-item"><Heart size={17} /> My companions</button>
        <button className="nav-item"><Brain size={17} /> Memory vault</button>
        <div className="side-bottom">
          <div className="privacy"><ShieldCheck size={17} /><span><b>Private workspace</b><small>Running on this device</small></span></div>
          <div className="version">NAZI AI · LOCAL BUILD 0.1</div>
        </div>
      </aside>

      <section className="main-panel">
        <header className="topbar"><span>PERSONAL AI COMPANION</span><div className="local-pill"><i /> LOCAL MODE</div></header>
        <div className="content">
          <div className="eyebrow"><Sparkles size={14} /> YOUR PRIVATE AI SPACE</div>
          <h1>A little world,<br /><em>made just for you.</em></h1>
          <p className="intro">Create a personality, shape the conversations, and build memories that stay on your computer.</p>

          <div className="hero-card">
            <div className="orb"><Heart size={32} fill="currentColor" /></div>
            <div className="hero-copy"><span className="card-kicker">YOUR FIRST COMPANION</span><h2>Someone new is waiting.</h2><p>Give your first AI companion a name, a personality, and a story of her own.</p></div>
            <button className="create-button"><Plus size={17} /> Create companion</button>
          </div>

          <div className="section-head"><div><span className="card-kicker">YOUR WORKSPACE</span><h2>Everything starts here</h2></div><span className="muted">Phase 1 · Foundation</span></div>
          <div className="feature-grid">
            <article className="feature-card"><div className="feature-icon pink"><Heart size={18} /></div><h3>Personality studio</h3><p>Define traits, tone, interests, backstory, and custom instructions.</p><span>COMING IN PHASE 2</span></article>
            <article className="feature-card"><div className="feature-icon violet"><Brain size={18} /></div><h3>Memory vault</h3><p>Keep meaningful moments and retrieve the right memories later.</p><span>COMING IN PHASE 3</span></article>
            <article className="feature-card"><div className="feature-icon blue"><MessageCircle size={18} /></div><h3>Private conversations</h3><p>Chat history stored in your local database, under your control.</p><span>COMING IN PHASE 2</span></article>
          </div>
          <footer className="status-footer"><span className={health ? "status-dot" : "status-dot offline"} />{health ? "Backend connected · SQLite ready · Local mode" : "Backend not detected · Start the local API to connect"}<span className="footer-right">YOUR DATA. YOUR DEVICE.</span></footer>
        </div>
      </section>
    </main>
  );
}
