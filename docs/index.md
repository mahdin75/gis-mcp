---
title: Home
hide:
  - navigation
  - toc
  - footer
---

<!--
  Landing page for GIS MCP Server
  - Fullscreen dark-blue hero
  - Custom top navigation bar
  - Centered CTA button (Getting Started)
  Tip: To add a background image later, set --hero-bg-image to your image URL.
-->

<style>
/* Remove MkDocs Material wrappers on the homepage only */
html, body { height: 100%; width: 100%; margin: 0; padding: 0; }
.md-header, .md-footer, .md-sidebar--primary, .md-sidebar--secondary { display: none; }
.md-container { max-width: none; width: 100%; margin: 0; padding: 0; }
.md-main { padding-top: 0 !important; margin-top: 0 !important; min-height: 100vh; }
.md-main__inner { margin: 0; max-width: none; width: 100%; }
.md-grid { max-width: none; width: 100%; padding: 0; }
.md-content { margin: 0; padding: 0; max-width: none; width: 100%; }
.md-content__inner { margin: 0; padding: 0; max-width: none; width: 100%; }
.md-content__inner:before { content: ""; display: block; height: 0 !important; }

:root {
  /* Cancel default header offset when header is hidden */
  --md-header-height: 0px;
  --nav-height: 64px;
  --brand-accent: #7cc5ff;
  --brand-blue-900: #0b1b2b;
  --brand-blue-800: #0f2740;
  --brand-blue-700: #143352;
  --text-on-dark: #e6eef7;
  --muted-on-dark: #b8c7d9;
  --hero-bg-image: url('bg-1.png');
}

.landing-page {
  position: relative;
  width: 100vw;
  min-height: 100vh;
  padding: 0;
  margin: 0;
  background: radial-gradient(1200px 800px at 20% 10%, var(--brand-blue-700), transparent 60%),
              radial-gradient(1000px 700px at 80% 20%, var(--brand-blue-800), transparent 55%),
              linear-gradient(180deg, var(--brand-blue-900), var(--brand-blue-800));
  color: var(--text-on-dark);
  overflow: hidden;
}

.landing-page::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image: var(--hero-bg-image);
  background-size: cover;
  background-position: center;
  opacity: 0.25;
  pointer-events: none;
}

.landing-page::after {
  content: "";
  position: absolute;
  inset: -50% -50%;
  background: radial-gradient(2px 2px at 20% 30%, rgba(255,255,255,0.08), transparent 60%),
              radial-gradient(1.5px 1.5px at 70% 20%, rgba(255,255,255,0.06), transparent 60%),
              radial-gradient(2px 2px at 40% 80%, rgba(255,255,255,0.07), transparent 60%);
  transform: translateZ(0);
  animation: floatDots 40s linear infinite;
  pointer-events: none;
}

@keyframes floatDots {
  0% { transform: translate(0, 0); }
  50% { transform: translate(2%, -2%); }
  100% { transform: translate(0, 0); }
}

.landing-nav {
  position: relative;
  height: var(--nav-height);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  background: linear-gradient(180deg, rgba(8, 16, 28, 0.55), rgba(8, 16, 28, 0.05));
  backdrop-filter: blur(6px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  z-index: 2;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 700;
  letter-spacing: 0.2px;
}

.brand .dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: linear-gradient(145deg, var(--brand-accent), #b0e1ff);
  box-shadow: 0 0 18px rgba(124, 197, 255, 0.7);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 18px;
}

.nav-links a {
  color: var(--muted-on-dark);
  text-decoration: none;
  font-weight: 500;
}

.nav-links a:hover { color: #ffffff; }

.hero {
  position: relative;
  min-height: calc(100vh - var(--nav-height));
  display: grid;
  place-items: center;
  text-align: center;
  padding: 48px 24px 64px;
}

.hero-inner {
  max-width: 980px;
  z-index: 1;
}

.eyebrow {
  display: inline-block;
  padding: 6px 12px;
  margin-bottom: 16px;
  border-radius: 999px;
  background: rgba(124, 197, 255, 0.14);
  color: #dff1ff;
  font-size: 12px;
  letter-spacing: 0.8px;
  text-transform: uppercase;
}

.hero h1 {
  margin: 0 0 10px 0;
  font-size: clamp(34px, 6vw, 64px);
  line-height: 1.05;
  letter-spacing: 0.2px;
  color: #ffffff;
}

.slogan {
  margin: 6px 0 18px 0;
  color: #dff1ff;
  font-weight: 600;
  letter-spacing: 0.2px;
}

.hero p.sub {
  margin: 0 auto 28px auto;
  max-width: 760px;
  color: var(--muted-on-dark);
  font-size: clamp(16px, 1.8vw, 20px);
}

.cta-row {
  display: flex;
  gap: 14px;
  justify-content: center;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 14px 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: #0a1726;
  background: linear-gradient(180deg, #bfe7ff, #7cc5ff);
  text-decoration: none;
  font-weight: 700;
  letter-spacing: 0.2px;
  box-shadow: 0 6px 24px rgba(124, 197, 255, 0.35);
}

.btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 28px rgba(124, 197, 255, 0.45);
}

.btn.secondary {
  color: var(--text-on-dark);
  background: linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
  border: 1px solid rgba(255, 255, 255, 0.16);
  box-shadow: none;
}

.footnote {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(230, 238, 247, 0.65);
  font-size: 12px;
}

@media (max-width: 720px) {
  .nav-links { display: none; }
}
</style>

<div class="landing-page">
  <header class="landing-nav">
    <div class="brand">
      <span class="dot"></span>
      <span>GIS MCP Server</span>
    </div>
    <nav class="nav-links">
      <a href="getting-started/">Getting Started</a>
      <a href="architecture/">Architecture</a>
      <a href="gis-ai-agent/">GIS AI Agent</a>
      <a href="install/">Installations</a>
      <a href="api/shapely/">API Reference</a>
      <a href="examples/">Examples</a>
      <a href="contributing/">Contributing</a>
      <a href="https://github.com/mahdin75/gis-mcp" target="_blank" rel="noopener">GitHub</a>
    </nav>
  </header>

  <section class="hero">
    <div class="hero-inner">
      <span class="eyebrow">Model Context Protocol · Geospatial</span>
      <h1>Bring real GIS analysis to your AI assistants.</h1>
      <div class="slogan">GIS MCP Server is the backend for your GIS AI Agent</div>
      <p class="sub">The MCP server that connects GIS Libraries(Shapely, PyProj, GeoPandas, Rasterio, and PySAL, etc) to LLMs — enabling precise geospatial operations, projections, raster processing, and spatial statistics in natural language workflows.</p>
      <div class="cta-row">
        <a class="btn" href="gis-ai-agent/">Build GIS AI Agent</a>
        <a class="btn secondary" href="api/shapely/">Explore API</a>
      </div>
    </div>
    
  </section>
</div>
