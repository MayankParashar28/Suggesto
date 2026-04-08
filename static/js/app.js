/**
 * Suggesto — Hand-Drawn Discovery Client
 * Optimized Overhaul — Billboard Hero & Discovery Tabs
 */

let currentTab = 'movies';
let currentGenre = 'All';
const TMDB_POSTER = 'https://image.tmdb.org/t/p/w500';
const cache = {};

const grid = document.getElementById('discovery-results');
const input = document.getElementById('query-input');
const detailView = document.getElementById('detail-view');
const genrePills = document.getElementById('genre-pills');
const spotlightContainer = document.getElementById('spotlight-container');

const CATEGORIES = {
    movies: ['All', 'Bollywood', 'Action', 'Sci-Fi', 'Horror', 'Romance', 'Comedy', 'Drama'],
    songs: ['All', 'Bollywood', 'Pop', 'Rock', 'Electronic', 'Jazz', 'Chill', 'Dance']
};

window.onload = () => {
    if (typeof lucide !== 'undefined') lucide.createIcons();
    renderPills();
    fetchDiscovery();
};

input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSearch(input.value.trim());
});

function switchTab(tab, el) {
    currentTab = tab;
    currentGenre = 'All';
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    el.classList.add('active');
    
    if (detailView) detailView.style.display = 'none';
    renderPills();
    fetchDiscovery();
}

/**
 * FETCH LOGIC
 */
async function fetchDiscovery() {
    console.log("🎨 Hand-drawing discovery...");
    grid.innerHTML = '<div style="padding:40px; text-align:center; opacity:0.5; font-family:var(--font-header);">🖋️ Sketching items for you...</div>';
    try {
        const res = await fetch(`/api/v1/discover/${currentTab}?limit=24`);
        if (!res.ok) throw new Error("Server was having trouble sketching...");
        const data = await res.json();
        const items = data.results || [];
        
        if (items.length === 0) {
            grid.innerHTML = '<div style="padding:40px; text-align:center; font-family:var(--font-header);">✍️ No sketches found in this wing of the gallery.</div>';
            return;
        }

        // Cache management for movies
        if (currentTab === 'movies') {
            items.forEach(item => {
                if (item.cached && item.tmdbId > 0) cache[item.tmdbId] = item.cached;
            });
        }
        
        // Pick one for Spotlight
        renderSpotlight(items[0]);
        renderItems(items.slice(1)); // Rest in the grid
        
        // Batch fetch
        if (currentTab === 'movies') {
            const uncached = items.filter(i => i.tmdbId > 0 && !cache[i.tmdbId]).map(i => i.tmdbId);
            if (uncached.length > 0) batchFetchMeta(uncached);
        }
    } catch (err) {
        console.error("Discovery error:", err);
        grid.innerHTML = `<div style="padding:40px; text-align:center; color:var(--accent); font-family:var(--font-header);">⚠️ Oops! The pencil broke: ${err.message}</div>`;
    }
}

async function handleSearch(q) {
    if (q.length < 2) return;
    try {
        const res = await fetch(`/api/v1/${currentTab}/search?q=${encodeURIComponent(q)}&limit=24`);
        const data = await res.json();
        const items = data.results || data;
        renderItems(items);
        if (currentTab === 'movies') {
            const uncached = items.filter(i => i.tmdbId > 0 && !cache[i.tmdbId]).map(i => i.tmdbId);
            if (uncached.length > 0) batchFetchMeta(uncached);
        }
    } catch (err) {
        console.error("Search error:", err);
    }
}

/**
 * RENDERING LOGIC
 */
function renderPills() {
    if (!genrePills) return;
    genrePills.innerHTML = '';
    CATEGORIES[currentTab].forEach(cat => {
        const p = document.createElement('button');
        p.className = `pill ${currentGenre === cat ? 'active' : ''}`;
        p.textContent = cat;
        p.onclick = () => {
            currentGenre = cat;
            document.querySelectorAll('.pill').forEach(btn => btn.classList.remove('active'));
            p.classList.add('active');
            handleGenreClick(cat);
        };
        genrePills.appendChild(p);
    });
}

function handleGenreClick(genre) {
    if (genre === 'All') fetchDiscovery();
    else handleSearch(genre);
}

const featuredItems = new Map();

function renderSpotlight(item) {
    if (!spotlightContainer || !item) return;
    const itemId = item.movieId || item.spotifyId;
    featuredItems.set(String(itemId), item);
    
    const isMusic = !!item.artist;
    const meta = !isMusic && cache[item.tmdbId];
    const image = isMusic ? generateMusicArt(item) : 
                (meta && meta.poster_path ? `<img src="${TMDB_POSTER}${meta.poster_path}" alt="">` : generateMovieSketch(item));

    spotlightContainer.innerHTML = `
        <div class="hero-card" onclick="selectItemById('${itemId}')">
            <div class="hero-img">${image}</div>
            <div class="hero-content">
                <div class="hero-tag">PICK OF THE DAY</div>
                <h1 class="hero-title">${item.title}</h1>
                <p class="hero-desc">${!isMusic ? (meta && meta.overview ? meta.overview : 'A classic sketch in the vault...') : `A track from "${item.album || 'Unknown'}" by ${item.artist}.`}</p>
                <div class="detail-meta">
                    <span>${item.releaseYear || ''}</span>
                    ${isMusic ? `<span class="acoustic-badge">${Math.round(item.tempo)} BPM</span>` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderItems(items) {
    if (!grid) return;
    grid.innerHTML = '';
    
    // Memory hygiene: cap the cache to avoid leaks
    if (featuredItems.size > 200) featuredItems.clear();

    items.forEach((item, i) => {
        const itemId = item.movieId || item.spotifyId;
        featuredItems.set(String(itemId), item);
        
        const card = document.createElement('div');
        card.className = 'card';
        card.dataset.tmdbId = item.tmdbId || '';
        const rot = (Math.random() * 4 - 2).toFixed(1);
        card.style.setProperty('--rand-rot', `${rot}deg`);
        card.style.animationDelay = `${i * 0.05}s`;
        card.onclick = () => selectItemById(itemId);

        const isMusic = !!item.artist;
        const meta = !isMusic && cache[item.tmdbId];
        
        let imageHtml = isMusic ? generateMusicArt(item) : 
                    (meta && meta.poster_path ? `<img src="${TMDB_POSTER}${meta.poster_path}" class="loaded" loading="lazy" decoding="async">` : 
                    (item.tmdbId > 0 ? `<img src="" id="img-${item.tmdbId}" class="skeleton" loading="lazy">` : generateMovieSketch(item)));

        card.innerHTML = `
            <div class="match-label">${isMusic ? 'Draft' : 'Picked'}</div>
            <div class="card-img">${imageHtml}</div>
            <div class="card-title">${item.title}</div>
            <div class="card-meta-line">
                <span>${isMusic ? item.artist : item.releaseYear}</span>
                ${item.vote_average ? `<span class="rating">⭐ ${item.vote_average.toFixed(1)}</span>` : ''}
            </div>
        `;
        grid.appendChild(card);
    });
}

function selectItemById(id) {
    const item = featuredItems.get(String(id));
    if (item) selectItem(item);
}

/**
 * UTILS & LEGACY WRAPPERS
 */
async function selectItem(item) {
    if (!detailView) return;
    detailView.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    document.getElementById('det-title').textContent = item.title;
    const isMusic = !!item.artist;
    const imgContainer = document.getElementById('det-img-container');

    if (isMusic) {
        imgContainer.innerHTML = generateMusicArt(item);
        document.getElementById('det-tagline').textContent = item.artist;
        document.getElementById('det-desc').textContent = `Featured in "${item.album || 'Single'}".`;
        document.getElementById('det-meta').innerHTML = `<span>${item.releaseYear}</span> <span class="acoustic-badge">${Math.round(item.tempo)} BPM</span>`;
    } else {
        let meta = cache[item.tmdbId];
        if (!meta && item.tmdbId > 0) {
            const res = await fetch(`/api/v1/tmdb/movie/${item.tmdbId}`);
            meta = await res.json();
            cache[item.tmdbId] = meta;
        }
        meta = meta || {};
        imgContainer.innerHTML = meta.poster_path ? `<img src="${TMDB_POSTER + meta.poster_path}">` : generateMovieSketch(item);
        document.getElementById('det-tagline').textContent = meta.tagline || "";
        document.getElementById('det-desc').textContent = meta.overview || "";
        document.getElementById('det-meta').innerHTML = `<span>${meta.release_date?.split('-')[0] || ''}</span> <span>${meta.runtime ? meta.runtime + 'm' : ''}</span>`;
    }
    
    // Update Play Link
    const playLink = document.getElementById('det-play-link');
    const playText = document.getElementById('det-play-text');
    if (playLink && playText) {
        if (isMusic && item.spotifyId) {
            playLink.href = `https://open.spotify.com/track/${item.spotifyId}`;
            playText.textContent = "Play on Spotify";
            playLink.style.display = "inline-flex";
        } else if (!isMusic && item.tmdbId > 0) {
            playLink.href = `https://www.themoviedb.org/movie/${item.tmdbId}`;
            playText.textContent = "Experience on TMDB";
            playLink.style.display = "inline-flex";
        } else {
            playLink.style.display = "none";
        }
    }

    lucide.createIcons();
    detailView.scrollIntoView({ behavior: 'smooth' });
}

async function batchFetchMeta(tmdbIds) {
    try {
        const res = await fetch('/api/v1/tmdb/batch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids: tmdbIds })
        });
        const data = await res.json();
        const results = data.results || {};
        for (const [tid, meta] of Object.entries(results)) {
            cache[parseInt(tid)] = meta;
            const card = document.querySelector(`.card[data-tmdb-id="${tid}"]`);
            if (card) updateCard(parseInt(tid), card, meta);
        }
    } catch (err) {}
}

function updateCard(tid, cardEl, data) {
    const img = cardEl.querySelector(`#img-${tid}`);
    if (img && data.poster_path) {
        img.src = TMDB_POSTER + data.poster_path;
        img.onload = () => { img.classList.remove('skeleton'); img.classList.add('loaded'); };
    }
}

/**
 * SKETCH ENGINE
 */
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
    const seed = (item.title || 'Unknown') + (item.artist || item.releaseYear || '');
    const rng = seedRandom(seed);
    const paperType = rng() > 0.5 ? 'dot-paper' : 'graph-paper';
    const paths = [ generateScribblePath(rng, 300, 450), generateScribblePath(rng, 300, 450) ];
    const subText = mode === 'music' ? (item.artist || '') : (item.releaseYear || 'Cinema');
    return `<div class="sketch-canvas ${paperType}"><svg class="sketch-svg" viewBox="0 0 300 450"><path d="${paths[0]}" stroke-width="1.5" opacity="0.1" /><path d="${paths[1]}" stroke-width="1" opacity="0.05" /></svg><div class="sketch-hero-text">${item.title}</div><div class="sketch-sub-text">${subText}</div></div>`;
}
/**
 * 'SKETCHY' THE MASCOT ENGINE
 */
const sketchyQuotes = [
    "Searching for a masterpiece? 🖋️",
    "Did you know? 'Dilwale Dulhania Le Jayenge' is the longest-running film! 🍿",
    "Listening to Bolly-beats today? 🎸",
    "I've sketched 180,000 items so far... whew!",
    "That Hero Card looks stunning, doesn't it?",
    "Need a recommendation? Try searching 'Sci-Fi'!",
    "I'm feeling wobbly today! 🤖"
];

function initMascot() {
    const mascot = document.getElementById('sketchy-mascot');
    if (!mascot) return;

    // Occasionally change quote
    setInterval(() => {
        if (!mascot.classList.contains('active')) {
            const text = document.getElementById('sketchy-text');
            if (text) text.textContent = sketchyQuotes[Math.floor(Math.random() * sketchyQuotes.length)];
        }
    }, 10000);

    // Initial sequence: Walk to logo
    setTimeout(() => moveMascotTo('at-logo'), 1000);
    
    // Recurring Patrol: Every 45 seconds, walk to a new navbar spot
    setInterval(() => {
        if (!mascot.classList.contains('active')) {
            const spots = ['at-logo', 'at-navbar', 'at-hero'];
            const next = spots[Math.floor(Math.random() * spots.length)];
            moveMascotTo(next);
        }
    }, 45000);
}

const mascotAnims = ["Wave", "Jump", "ThumbsUp", "Yes", "Dance"];

function moveMascotTo(state) {
    const mascot = document.getElementById('sketchy-mascot');
    const model = document.getElementById('sketchy-3d');
    if (!mascot || !model) return;

    // Determine direction: if moving TO logo, face LEFT. Else face RIGHT.
    if (state === 'at-logo') {
        mascot.classList.add('facing-left');
    } else {
        mascot.classList.remove('facing-left');
    }

    model.setAttribute('animation-name', 'Walking');

    const states = ['at-navbar', 'at-hero', 'at-logo'];
    states.forEach(s => mascot.classList.remove(s));
    mascot.classList.add(state);

    // Sync arrival
    const onArrival = () => {
        model.setAttribute('animation-name', 'Wave');
        mascot.removeEventListener('transitionend', onArrival);
        setTimeout(() => {
            if (model.getAttribute('animation-name') === 'Wave') {
                model.setAttribute('animation-name', 'Idle');
            }
        }, 3000);
    };
    mascot.addEventListener('transitionend', onArrival);
}

function triggerSketchy3D() {
    const mascot = document.getElementById('sketchy-mascot');
    const model = document.getElementById('sketchy-3d');
    const text = document.getElementById('sketchy-text');
    if (!mascot || !model || !text) return;

    mascot.classList.add('active');
    
    // Pick a random behavior
    const behaviors = [
        { anim: "Jump", text: "Boing! Searching... 🚀" },
        { anim: "ThumbsUp", text: "Great choice! 👍" },
        { anim: "Dance", text: "Let's celebrate this sketch! 🕺" }
    ];
    const behavior = behaviors[Math.floor(Math.random() * behaviors.length)];
    
    model.setAttribute('animation-name', behavior.anim);
    text.textContent = behavior.text;
    
    // Walk to a new navbar spot after the animation
    const locations = ['at-navbar', 'at-hero', 'at-logo'];
    const nextLoc = locations[Math.floor(Math.random() * locations.length)];
    setTimeout(() => moveMascotTo(nextLoc), 1500);
    
    setTimeout(() => {
        mascot.classList.remove('active');
    }, 4000);
}

function generateMusicArt(item) { return generateMasterpieceSketch(item, 'music'); }
function generateMovieSketch(item) { return generateMasterpieceSketch(item, 'movie'); }

// Initialize mascot logic
window.onload = (originalOnload => {
    return () => {
        if (originalOnload) originalOnload();
        initMascot();
    };
})(window.onload);
