const architecture = {
  primaryStack: "React + TypeScript + Vite",
  fallbackStack: "Standalone serious viewer HTML",
  authority: "Python simulator remains authoritative",
  transport: "Simulation API bundles now, live session transport next",
};

function App(): JSX.Element {
  return (
    <div className="shell">
      <header className="masthead panel">
        <div>
          <p className="eyebrow">Step 41 Foundation</p>
          <h1>Autonomous Ops Serious UI</h1>
          <p className="lede">
            This empty shell locks the serious frontend direction without
            changing simulator authority or pre-implementing later UI steps.
          </p>
        </div>
        <div className="badge-row" aria-label="Architecture decisions">
          <span className="badge">Primary: {architecture.primaryStack}</span>
          <span className="badge">Fallback: {architecture.fallbackStack}</span>
        </div>
      </header>

      <main className="workspace">
        <section className="stage panel" aria-labelledby="scene-title">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Scene Region</p>
              <h2 id="scene-title">Renderer Placeholder</h2>
            </div>
            <span className="status-pill">SVG scene baseline</span>
          </div>
          <div className="stage-canvas" role="img" aria-label="Placeholder scene">
            <div className="grid-overlay" />
            <div className="focus-card">
              <strong>Next steps start here</strong>
              <p>
                Camera control, layer toggles, hover, selection, and live bundle
                binding land in later steps.
              </p>
            </div>
          </div>
        </section>

        <aside className="sidebar">
          <section className="panel info-panel">
            <p className="eyebrow">Authority</p>
            <h2>Backend / Frontend Split</h2>
            <ul className="detail-list">
              <li>{architecture.authority}</li>
              <li>Frontend consumes derived bundle and session surfaces.</li>
              <li>Typed commands remain the only control path.</li>
            </ul>
          </section>

          <section className="panel info-panel">
            <p className="eyebrow">Transport Assumption</p>
            <h2>Compatibility First</h2>
            <ul className="detail-list">
              <li>{architecture.transport}</li>
              <li>Replay, live session, and live sync stay versioned.</li>
              <li>No direct mutation of simulator internals from the UI.</li>
            </ul>
          </section>

          <section className="panel info-panel">
            <p className="eyebrow">Shell Regions</p>
            <h2>Reserved Layout</h2>
            <ul className="detail-list">
              <li>Toolbar and session metadata</li>
              <li>Scene viewport and future minimap</li>
              <li>Timeline, command center, inspector, and alerts</li>
            </ul>
          </section>
        </aside>
      </main>
    </div>
  );
}

export default App;
