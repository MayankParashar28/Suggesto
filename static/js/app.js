/**
 * Suggesto — Hand-Drawn Discovery Client
 * Stable "Masterpiece Edition"
 */

let currentTab = 'movies';
const TMDB_POSTER = 'https://image.tmdb.org/t/p/w500';
const cache = {};

const input = document.getElementById('query-input');
const grid = document.getElementById('discovery-results');
const header = document.getElementById('grid-header');
const detailView = document.getElementById('detail-view');

window.onload = () => {
    if (typeof lucide !== "undefined") lucide.createIcons();
    handleDiscover('Inception');
};

input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleDiscover(input.value.trim());
});

function switchTab(tab, el) {
    currentTab = tab;
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    el.classList.add('active');
    if (detailView) detailView.style.display = 'none';

    if (header) {
        if (tab === 'movies') header.textContent = 'The Cinema Log';
        else if (tab === 'songs') header.textContent = 'The Playlist Scribbles';
        else if (tab === 'courses') header.textContent = 'The Study Notes';
    }

    if (tab === 'movies') handleDiscover('Inception');
    else if (tab === 'songs') handleDiscover('The');
    else {
        grid.innerHTML = `<div style="padding: 40px; text-align: center; font-family: var(--font-header);">✍️ Section is being sketched...</div>`;
    }
}

async function handleDiscover(q) {
    if (q.length < 2) return;
    const searchBox = document.querySelector('.search-box');
    if (searchBox) searchBox.style.borderColor = "var(--accent)";
    
    try {
        const category = currentTab === 'movies' ? 'movies' : 'songs';
        const res = await fetch(`/api/v1/${category}/search?q=${encodeURIComponent(q)}&limit=24`);
        const data = await res.json();
        renderItems(data.results || data);
    } catch (err) {
        console.error("Discovery error:", err);
    } finally {
        if (searchBox) searchBox.style.borderColor = "var(--foreground)";
    }
}

function renderItems(items) {
    if (!grid) return;
    grid.innerHTML = '';
    if (!Array.isArray(items)) items = [];

    items.forEach((item, i) => {
        const card = document.createElement('div');
        card.className = 'card';
        const rot = (Math.random() * 4 - 2).toFixed(1);
        card.style.setProperty('--rand-rot', `${rot}deg`);
        card.style.animationDelay = `${i * 0.05}s`;
        card.onclick = () => selectItem(item);

        const isMusic = !!item.artist;
        const metadataHtml = isMusic ? 
            `<span>${item.artist}</span> <span style="opacity:0.3">|</span> <span>${item.album || ''}</span>` :
            `<span class="rating" id="rate-${item.tmdbId}"></span> <span style="opacity:0.3">|</span> <span>${item.releaseYear || ''}</span>`;

        const imageHtml = isMusic ? generateMusicArt(item) : `<img src="" id="img-${item.tmdbId}" class="skeleton">`;

        card.innerHTML = `
            <div class="match-label">${isMusic ? 'Draft' : 'Picked'}</div>
            <div class="card-img">${imageHtml}</div>
            <div class="card-title">${item.title}</div>
            <div class="card-meta-line" style="flex-direction: column; align-items: start; gap: 4px;">
                ${metadataHtml}
                ${isMusic && item.tempo ? `<div style="display:flex; gap:4px; flex-wrap:wrap">
                    <span class="acoustic-badge">${Math.round(item.tempo)} BPM</span>
                    ${item.energy > 0.7 ? '<span class="acoustic-badge energy-high">🔥 Intense</span>' : ''}
                </div>` : ''}
            </div>
        `;
        grid.appendChild(card);
        if (!isMusic) fetchMeta(item.tmdbId, card);
    });
}

async function fetchMeta(tid, cardEl) {
    if (!tid || tid <= 0) return;
    if (cache[tid]) return updateCard(tid, cardEl, cache[tid]);
    try {
        const res = await fetch(`/api/v1/tmdb/movie/${tid}`);
        const data = await res.json();
        cache[tid] = data;
        updateCard(tid, cardEl, data);
    } catch (err) {}
}

function updateCard(tid, cardEl, data) {
    const img = cardEl.querySelector(`#img-${tid}`);
    if (img) {
        if (data.poster_path) {
            img.src = TMDB_POSTER + data.poster_path;
            img.onload = () => img.classList.add('loaded');
        } else {
            const container = cardEl.querySelector('.card-img');
            if (container) container.innerHTML = generateMovieSketch(data);
        }
    }
    const rate = cardEl.querySelector(`#rate-${tid}`);
    if (rate && data.vote_average) rate.innerHTML = `<i data-lucide="star" style="width:12px;fill:var(--accent);color:var(--accent)"></i> ${data.vote_average.toFixed(1)}`;
}

async function selectItem(item) {
    if (!detailView) return;
    detailView.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    document.getElementById('det-title').textContent = item.title;
    const isMusic = !!item.artist;

    if (isMusic) {
        document.getElementById('det-img-container').innerHTML = generateMusicArt(item);
        document.getElementById('det-tagline').textContent = item.artist;
        document.getElementById('det-desc').textContent = `${item.title} featured in "${item.album || 'Single'}".`;
        document.getElementById('det-meta').innerHTML = `<span>${item.releaseYear}</span> <span class="acoustic-badge">${Math.round(item.tempo)} BPM</span>`;
    } else {
        const meta = cache[item.tmdbId] || await (await fetch(`/api/v1/tmdb/movie/${item.tmdbId}`)).json();
        document.getElementById('det-img-container').innerHTML = meta.poster_path ? `<img src="${TMDB_POSTER+meta.poster_path}">` : generateMovieSketch(item);
        document.getElementById('det-tagline').textContent = meta.tagline || "";
        document.getElementById('det-desc').textContent = meta.overview;
        document.getElementById('det-meta').innerHTML = `<span>${meta.release_date?.split('-')[0]}</span> <span>${meta.runtime}m</span>`;
    }
}

/* ── Masterpiece Sketch Engine ── */
function seedRandom(seed) {
    let s = 0;
    for (let i = 0; i < seed.length; i++) s = seed.charCodeAt(i) + ((s << 5) - s);
    return function() { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}

function generateScribblePath(rng, w, h) {
    const pts = [];
    for (let i =0; i<5; i++) pts.push(`${Math.floor(rng()*w)},${Math.floor(rng()*h)}`);
    return `M ${pts.join(' L ')} Z`;
}

function generateMasterpieceSketch(item, mode = 'music') {
    const seed = item.title + (item.artist || item.releaseYear || '');
    const rng = seedRandom(seed);
    const paperType = rng() > 0.5 ? 'dot-paper' : 'graph-paper';
    const paths = [ generateScribblePath(rng, 300, 450), generateScribblePath(rng, 300, 450) ];
    const subText = mode === 'music' ? item.artist : (item.releaseYear || 'Cinema');

    return `
        <div class="sketch-canvas ${paperType}">
            <svg class="sketch-svg" viewBox="0 0 300 450">
                <path d="${paths[0]}" stroke-width="1.5" opacity="0.1" />
                <path d="${paths[1]}" stroke-width="1" opacity="0.05" transform="rotate(5, 150, 225)" />
            </svg>
            <div class="sketch-hero-text">${item.title}</div>
            <div class="sketch-sub-text">${subText}</div>
        </div>
    `;
}

function generateMusicArt(item) { return generateMasterpieceSketch(item, 'music'); }
function generateMovieSketch(item) { return generateMasterpieceSketch(item, 'movie'); }
