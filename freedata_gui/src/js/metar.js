// METAR parsing, flight category, formatters, and wind compass SVG.

export function parseMetar(raw) {
  const out = {
    iata: null,
    day: null, hh: null, mm: null,
    wind: { dir_deg: null, spd_kt: null, gust_kt: null, var_from: null, var_to: null },
    visibility: { code: null, meters: null },
    temp_c: null,
    dew_c: null,
    qnh_hpa: null,
    auto: false,
    cor: false,
    clouds: [],
    raw: raw?.trim() || ''
  };
  if (!raw) return out;

  const tokens = raw.replace('=', '').trim().split(/\s+/);

  out.auto = tokens.includes('AUTO');
  out.cor  = tokens.includes('COR');

  for (const t of tokens) {
    if (/^[A-Z]{3}$/.test(t)) { out.iata = t; break; }
  }

  const tTok = tokens.find(t => /^\d{6}Z$/.test(t));
  if (tTok) {
    out.day = tTok.slice(0,2);
    out.hh  = tTok.slice(2,4);
    out.mm  = tTok.slice(4,6);
  }

  const wTok = tokens.find(t => /^(?:\d{3}|VRB)\d{2,3}(G\d{2,3})?KT$/.test(t));
  if (wTok) {
    const m = wTok.match(/^(\d{3}|VRB)(\d{2,3})(?:G(\d{2,3}))?KT$/);
    if (m) {
      out.wind.dir_deg = m[1] === 'VRB' ? null : parseInt(m[1], 10);
      out.wind.spd_kt  = parseInt(m[2], 10);
      out.wind.gust_kt = m[3] ? parseInt(m[3], 10) : null;
    }
  }
  const vTok = tokens.find(t => /^\d{3}V\d{3}$/.test(t));
  if (vTok) {
    const m = vTok.match(/^(\d{3})V(\d{3})$/);
    out.wind.var_from = parseInt(m[1], 10);
    out.wind.var_to   = parseInt(m[2], 10);
  }

  if (tokens.includes('CAVOK')) {
    out.visibility.code = 'CAVOK';
    out.visibility.meters = 10000;
  } else {
    const vis = tokens.find(t => /^\d{4}$/.test(t));
    if (vis) {
      out.visibility.code = vis;
      out.visibility.meters = parseInt(vis, 10);
    }
  }

  const tdTok = tokens.find(t => /^(M?\d{1,2})\/(M?\d{1,2})$/.test(t));
  if (tdTok) {
    const m = tdTok.match(/^(M?\d{1,2})\/(M?\d{1,2})$/);
    out.temp_c = _signed(m[1]);
    out.dew_c  = _signed(m[2]);
  }

  const qTok = tokens.find(t => /^(Q\d{4}|A\d{4})$/.test(t));
  if (qTok) {
    if (qTok.startsWith('Q')) out.qnh_hpa = parseInt(qTok.slice(1), 10);
    else {
      const inHg = parseInt(qTok.slice(1), 10) / 100;
      out.qnh_hpa = Math.round(inHg * 33.8639);
    }
  }

  for (const t of tokens) {
    const m = t.match(/^(FEW|SCT|BKN|OVC)(\d{3})(CB|TCU)?$/);
    if (m) {
      out.clouds.push({
        cover: m[1],
        base_ft: parseInt(m[2], 10) * 100,
        type: m[3] || null
      });
    }
  }

  return out;
}

function _signed(s) { return s?.startsWith('M') ? -parseInt(s.slice(1),10) : parseInt(s,10); }

// ---------------- Flight Category ----------------

export function determineFlightCategory(parsed) {
  const cavok = parsed.visibility.code === 'CAVOK';
  let ceiling = null;
  for (const c of parsed.clouds || []) {
    if (c.cover === 'BKN' || c.cover === 'OVC') {
      if (ceiling === null || c.base_ft < ceiling) ceiling = c.base_ft;
    }
  }
  const v = parsed.visibility.meters ?? 0;
  if (cavok) return 'VFR';
  if (v >= 5000 && (ceiling === null || ceiling > 3000)) return 'VFR';
  if ((v >= 3000 && v < 5000) || (ceiling !== null && ceiling >= 1000 && ceiling <= 3000)) return 'MVFR';
  if ((v >= 1500 && v < 3000) || (ceiling !== null && ceiling >= 500 && ceiling < 1000)) return 'IFR';
  return 'LIFR';
}

export function categoryClass(cat) {
  switch (cat) {
    case 'VFR': return 'text-bg-success';
    case 'MVFR': return 'text-bg-primary';
    case 'IFR': return 'text-bg-danger';
    case 'LIFR': return 'text-bg-magenta';
    default: return 'text-bg-secondary';
  }
}

// ---------------- Formatters (labels shown in Vue) ----------------

export function windToString(w) {
  if (!w) return '—';
  const base = (w.dir_deg == null)
    ? `VRB/${w.spd_kt ?? 0}kt`
    : `${w.dir_deg}°/${w.spd_kt ?? 0}kt`;
  const gust = w.gust_kt ? ` G${w.gust_kt}` : '';
  const varrng = (w.var_from != null && w.var_to != null) ? ` V${w.var_from}-${w.var_to}` : '';
  return base + gust + varrng;
}

export function visibilityToString(v) {
  return v?.code || '—';
}

export function cloudsToString(clouds) {
  if (!clouds || clouds.length === 0) return '—';
  return clouds.map(c => `${c.cover}${String(Math.round(c.base_ft/100)).padStart(3,'0')}${c.type || ''}`).join(' ');
}

export function tempDewToString(t, d) {
  const tStr = (typeof t === 'number') ? `${t}` : '—';
  const dStr = (typeof d === 'number') ? `${d}` : '—';
  return `${tStr}/${dStr}°C`;
}

export function qnhToString(q) {
  return (typeof q === 'number') ? `${q} hPa` : '—';
}

export function timeToString(day, hh, mm) {
  return (day && hh && mm) ? `${day}.${hh}:${mm}Z` : '—';
}

// ---------------- SVG Compass + Windbarb (WMO-like) ----------------

export function buildCompassSVG(wind, opts = {}) {
  const size = opts.size ?? 160;
  const cx = size/2, cy = size/2;
  const dirDeg = wind?.dir_deg;
  const spd = wind?.spd_kt ?? 0;
  const gust = wind?.gust_kt;

  const showDir = (dirDeg == null) ? null : (dirDeg + 180) % 360;
  const transform = (showDir == null) ? '' : `transform="rotate(${showDir} ${cx} ${cy})"`;

  const svgGrid = `
    <circle cx="${cx}" cy="${cy}" r="${size*0.4375}" fill="none" stroke="#ced4da"/>
    <circle cx="${cx}" cy="${cy}" r="${size*0.3125}" fill="none" stroke="#e9ecef"/>
    <circle cx="${cx}" cy="${cy}" r="${size*0.1875}" fill="none" stroke="#f1f3f5"/>
    <line x1="${size*0.0625}" y1="${cy}" x2="${size*0.9375}" y2="${cy}" stroke="#dee2e6"/>
    <line x1="${cx}" y1="${size*0.0625}" x2="${cx}" y2="${size*0.9375}" stroke="#dee2e6"/>
    <text x="${cx}" y="${size*0.0375}" text-anchor="middle" font-size="10" fill="#6c757d">N</text>
    <text x="${size*0.9625}" y="${cy+4}" text-anchor="end" font-size="10" fill="#6c757d">E</text>
    <text x="${cx}" y="${size*0.975}" text-anchor="middle" font-size="10" fill="#6c757d">S</text>
    <text x="${size*0.0375}" y="${cy+4}" text-anchor="start" font-size="10" fill="#6c757d">W</text>
  `;

  let windGroup = `<circle cx="${cx}" cy="${cy}" r="10" stroke="#0d6efd" stroke-width="3" fill="none"/>`;

  if (dirDeg != null) {
    windGroup = `<g ${transform}>${_wmoBarb(cx, cy, spd, size)}</g>`;
  }

  const gustRing = (gust && gust > spd)
    ? `<circle cx="${cx}" cy="${cy}" r="${size*0.48}" fill="none" stroke="#0d6efd" stroke-dasharray="4 4" />`
    : '';

  return `
  <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="display:block;max-width:${size}px">
    ${svgGrid}
    ${windGroup}
    ${gustRing}
  </svg>`;
}

function _wmoBarb(cx, cy, spdKt, size) {
  const stroke = '#0d6efd';
  const lw = 3;
  const staffLen = size * 0.45;
  const step = Math.max(6, size * 0.05);
  const barbLong = Math.max(12, size * 0.10);
  const barbHalf  = barbLong * 0.6;

  let s = Math.round((spdKt || 0) / 5) * 5;
  const tri = Math.floor(s / 50); s -= tri * 50;
  const ten = Math.floor(s / 10); s -= ten * 10;
  const five = Math.floor(s / 5);

  const elems = [];
  elems.push(`<line x1="${cx}" y1="${cy}" x2="${cx}" y2="${cy - staffLen}" stroke="${stroke}" stroke-width="${lw}" />`);

  let y = cy - staffLen + step*1.2;
  for (let i = 0; i < tri; i++) {
    elems.push(`<polygon points="${cx},${y} ${cx},${y - step} ${cx + barbLong},${y - step/2}" fill="${stroke}" />`);
    y += step;
  }
  for (let i = 0; i < ten; i++) {
    elems.push(`<line x1="${cx}" y1="${y}" x2="${cx + barbLong}" y2="${y - barbLong*0.35}" stroke="${stroke}" stroke-width="${lw}" />`);
    y += step;
  }
  if (five) {
    elems.push(`<line x1="${cx}" y1="${y}" x2="${cx + barbHalf}" y2="${y - barbHalf*0.35}" stroke="${stroke}" stroke-width="${lw}" />`);
  }
  return elems.join('\n');
}
