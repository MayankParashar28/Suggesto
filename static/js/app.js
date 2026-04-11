/**
 * Inkpick — Hand-Drawn Discovery Hub
 * Consolidated & Stabilized — All Bugs Fixed
 */

let currentTab = 'movies';
let currentGenre = 'All';
const TMDB_POSTER = 'https://image.tmdb.org/t/p/w500';
const cache = {};
const CACHE_MAX = 500; // O6: Memory cap

// ── Elements (Resolved in init) ──────────────────────
let grid, input, detailView, genrePills, spotlightContainer;

function resolveElements() {
    grid = document.getElementById('discovery-results');
    input = document.getElementById('query-input');
    detailView = document.getElementById('detail-view');
    genrePills = document.getElementById('genre-pills');
    spotlightContainer = document.getElementById('spotlight-container');
    
    if (!grid) console.warn("⚠️ Warning: 'discovery-results' grid element not found.");
}

const CATEGORIES = {
    movies: ['All', 'Bollywood', 'Action', 'Sci-Fi', 'Horror', 'Romance', 'Comedy', 'Drama'],
    songs: ['All', 'Bollywood', 'Pop', 'Rock', 'Electronic', 'Jazz', 'Chill', 'Dance'],
    courses: ['All', 'YouTube', 'Web Dev', 'Design', 'Business', 'Music']
};

// Course fallback images by category (O7: No more Microlink)
const COURSE_FALLBACKS = {
    'web dev': 'https://images.unsplash.com/photo-1461749280684-dccba630e2f6?w=500&q=80',
    'design': 'https://images.unsplash.com/photo-1558655146-9f40138edfeb?w=500&q=80',
    'business': 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=500&q=80',
    'music': 'https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=500&q=80',
    'default': 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=500&q=80'
};

// ── B1 FIX: Single DOMContentLoaded handler ──────────
window.addEventListener('DOMContentLoaded', () => {
    console.log("🎨 Inkpick Hub: DOM Content Loaded. Initializing...");
    try {
        resolveElements();
        if (typeof lucide !== 'undefined') lucide.createIcons();
        initRouter();
        initMascot();
        initShortcuts();
        
        // Safety: Ensure visibility of main content
        const main = document.getElementById('main-content');
        if (main) main.style.opacity = '1';

        console.log("✅ Inkpick Hub initialized successfully.");
    } catch (err) {
        console.error("❌ Critical Hub Init Error:", err);
        // Show visible error if the core crashes
        const errGrid = document.getElementById('discovery-results');
        if (errGrid) {
            errGrid.innerHTML = `
                <div class="empty-state" style="color:var(--accent);">
                    <h3>⚠️ Hub initialization failure</h3>
                    <p>${err.message}</p>
                    <button onclick="location.reload()">Reload Hub</button>
                </div>`;
        }
    }
});

input?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleSearch(input.value.trim());
});

window.addEventListener('hashchange', initRouter);

function initRouter() {
    const hash = window.location.hash || '#/movies';
    const route = hash.replace('#/', '');
    const validRoutes = ['movies', 'songs', 'courses'];
    const tab = validRoutes.includes(route) ? route : 'movies';
    const navLink = document.querySelector(`.nav-link[data-route="${tab}"]`);
    internalSwitchTab(tab, navLink);
}

function internalSwitchTab(tab, el) {
    currentTab = tab;
    currentGenre = 'All';
    document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
    if (el) el.classList.add('active');

    // Paper clip
    movePaperClip(el);

    const titles = {
        movies: "Inkpick: Cinema Log 🎬",
        songs: "Inkpick: Playlist Scribbles 🎧",
        courses: "Inkpick: Learning Scribbles 📚"
    };
    document.title = titles[tab] || "Inkpick: Sketchbook";

    // Update placeholder
    if (input) {
        const ph = { movies: 'Sketch a movie title...', songs: 'Sketch a song or artist...', courses: 'Sketch a course topic...' };
        input.placeholder = ph[tab] || 'Search...';
    }

    if (detailView) detailView.style.display = 'none';
    renderPills();
    fetchDiscovery();

    // Mascot commentary
    const mascotConfig = {
        movies: { quote: "Cinema Log activated! 🍿", anim: "ThumbsUp" },
        songs: { quote: "Tuning into Playlist Scribbles! 🎸", anim: "Dance" },
        courses: { quote: "Learning mode: ON! 📚", anim: "Yes" }
    };
    const config = mascotConfig[tab] || { quote: "Sketching something fresh! 🖋️", anim: "Wave" };
    triggerSketchy3D(config.quote, config.anim);
}

function movePaperClip(el) {
    const clip = document.getElementById('nav-paper-clip');
    if (!clip || !el) return;
    const rect = el.getBoundingClientRect();
    const parentRect = el.parentElement.getBoundingClientRect();
    const left = rect.left - parentRect.left + (rect.width / 2);
    clip.style.left = `${left}px`;
    clip.style.transform = `translateX(-50%) rotate(${Math.random() * 20 - 10}deg)`;
}

function pruneCache() {
    const keys = Object.keys(cache);
    if (keys.length > CACHE_MAX) {
        // Remove oldest half
        keys.slice(0, Math.floor(CACHE_MAX / 2)).forEach(k => delete cache[k]);
    }
}

function initShortcuts() {
    window.addEventListener('keydown', (e) => {
        if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
            e.preventDefault();
            if (input) input.focus();
        }
    });
}

function showSkeletons(count = 12) {
    console.log(`🖋️ Sketching ${count} skeletons...`);
    if (!grid) return;
    
    let html = '';
    for (let i = 0; i < count; i++) {
        const rot = (Math.random() * 4 - 2).toFixed(1);
        html += `
            <div class="skeleton" style="transform: rotate(${rot}deg); animation-delay: ${i * 0.05}s;">
                <div class="skel-card">
                    <div class="skel-img"></div>
                    <div class="skel-title"></div>
                    <div class="skel-text"></div>
                </div>
            </div>`;
    }
    grid.innerHTML = html;
    grid.style.opacity = '1';
}


/**
 * FETCH LOGIC
 */
async function fetchDiscovery(append = false) {
    const loadMoreWrap = document.getElementById('load-more-wrap');
    if (!append) {
        console.log("🎨 Hand-drawing discovery...");
        showSkeletons(12);
        if (loadMoreWrap) loadMoreWrap.style.display = 'none';
    }

    try {
        const limit = 24;
        const res = await fetch(`/api/v1/discover/${currentTab}?limit=${limit}`);
        if (!res.ok) throw new Error("Server was having trouble sketching...");
        const data = await res.json();
        const items = data.results || [];

        if (!append && items.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <h3>✍️ No sketches found in this wing.</h3>
                    <p>Try switching categories or check back later!</p>
                </div>`;
            return;
        }

        // Cache management for movies
        if (currentTab === 'movies') {
            items.forEach(item => {
                if (item.cached && item.tmdbId > 0) cache[item.tmdbId] = item.cached;
            });
            pruneCache();
        }

        if (!append) {
            grid.innerHTML = '';
            renderSpotlight(items[0]);
            renderItems(items.slice(1));
        } else {
            renderItems(items);
        }

        // Show "Load More" if we got a full page
        if (loadMoreWrap) loadMoreWrap.style.display = items.length >= limit ? 'flex' : 'none';

        if (currentTab === 'movies') {
            const uncached = items.filter(i => i.tmdbId > 0 && !cache[i.tmdbId]).map(i => i.tmdbId);
            if (uncached.length > 0) batchFetchMeta(uncached);
        }
    } catch (err) {
        console.error("Discovery error:", err);
        grid.innerHTML = `<div class="empty-state" style="color:var(--accent);">⚠️ Pencil broke: ${err.message}</div>`;
    }
}

// Bind Load More
document.getElementById('btn-load-more')?.addEventListener('click', () => fetchDiscovery(true));


async function handleSearch(q) {
    if (q.length < 2) return;
    try {
        const res = await fetch(`/api/v1/${currentTab}/search?q=${encodeURIComponent(q)}&limit=24`);
        const data = await res.json();
        const items = data.results || data;

        renderItems(items);

        if (items.length === 0 && data.suggestion) {
            triggerSketchy3D(`Did you mean <span style="text-decoration:underline; cursor:pointer; color:var(--secondary);" onclick="applySuggestion('${data.suggestion.replace(/'/g, "\\'")}')">${data.suggestion}</span>?`, "Jump");
        } else if (currentTab === 'movies') {
            const uncached = items.filter(i => i.tmdbId > 0 && !cache[i.tmdbId]).map(i => i.tmdbId);
            if (uncached.length > 0) batchFetchMeta(uncached);
        }
    } catch (err) {
        console.error("Search error:", err);
    }
}

function applySuggestion(text) {
    if (input) {
        input.value = text;
        handleSearch(text);
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
    else if (genre === 'YouTube') handleSearch('YouTube');
    else handleSearch(genre);
}

const featuredItems = new Map();

function renderSpotlight(item) {
    if (!spotlightContainer || !item) return;
    const itemId = item.movieId || item.spotifyId;
    featuredItems.set(String(itemId), item);

    const isMusic = !!item.artist && item.tmdbId === -1;
    const isCourse = item.tmdbId === -2;
    const meta = !isMusic && !isCourse && cache[item.tmdbId];
    const image = isCourse ? generateCoursePoster(item) :
        (isMusic ? generateMusicArt(item) :
            (meta && meta.poster_path ? `<img src="${TMDB_POSTER}${meta.poster_path}" alt="">` : generateMovieSketch(item)));

    spotlightContainer.innerHTML = `
        <div class="hero-card ${isCourse ? 'course-hero' : ''}" onclick="selectItemById('${itemId}')">
            <div class="masking-tape top-left"></div>
            <div class="masking-tape top-right"></div>
            <div class="hero-img">${image}</div>
            <div class="hero-content">
                <div class="hero-tag">PICK OF THE DAY</div>
                <h1 class="hero-title">${item.title}</h1>
                <p class="hero-desc">${isCourse ? `A top-rated lesson from ${item.album}. Category: ${item.category}` : (!isMusic ? (meta && meta.overview ? meta.overview : 'A classic sketch in the vault...') : `A track from "${item.album || 'Unknown'}" by ${item.artist}.`)}</p>
                <div class="detail-meta">
                    <span>${item.releaseYear || ''}</span>
                    ${isMusic ? `<span class="acoustic-badge">${Math.round(item.tempo)} BPM</span>` : ''}
                    ${isCourse ? `<span class="academic-badge">${item.category}</span> <span class="rating">⭐ ${item.rating}</span>` : ''}
                </div>
            </div>
        </div>
    `;
}

function renderItems(items) {
    if (!grid) return;
    grid.innerHTML = '';
    if (featuredItems.size > 200) featuredItems.clear();

    items.forEach((item, i) => {
        const isMusic = item.tmdbId === -1;
        const isCourse = item.tmdbId === -2;
        const itemId = item.movieId || item.spotifyId;
        featuredItems.set(String(itemId), item);

        const card = document.createElement('div');
        card.className = `card ${isCourse ? 'course-item' : ''}`;
        card.dataset.tmdbId = item.tmdbId || '';
        const rot = (Math.random() * 4 - 2).toFixed(1);
        card.style.setProperty('--rand-rot', `${rot}deg`);
        card.style.animationDelay = `${i * 0.05}s`;
        card.onclick = () => selectItemById(itemId);

        const meta = !isMusic && !isCourse && cache[item.tmdbId];

        let imageHtml = isCourse ? generateCoursePoster(item) :
            (isMusic ? generateMusicArt(item) :
                (meta && meta.poster_path ? `<img src="${TMDB_POSTER}${meta.poster_path}" class="loaded" loading="lazy" decoding="async">` :
                    (item.tmdbId > 0 ? `<img src="" id="img-${item.tmdbId}" class="skeleton" loading="lazy">` : generateMovieSketch(item))));

        card.innerHTML = `
            <div class="match-label">${isMusic ? 'Draft' : (isCourse ? 'Lesson' : 'Picked')}</div>
            <div class="card-img">${imageHtml}</div>
            <div class="card-title">${item.title}</div>
            <div class="card-meta-line">
                <span>${isCourse ? item.artist : (isMusic ? item.artist : item.releaseYear)}</span>
                ${item.rating ? `<span class="rating">⭐ ${item.rating}</span>` : (item.vote_average ? `<span class="rating">⭐ ${item.vote_average.toFixed(1)}</span>` : '')}
            </div>
        `;
        grid.appendChild(card);
    });
}

function selectItemById(id) {
    const item = featuredItems.get(String(id));
    if (item) selectItem(item);
}

async function selectItem(item) {
    if (!detailView) return;
    detailView.style.display = 'block';
    window.scrollTo({ top: 0, behavior: 'smooth' });
    document.getElementById('det-title').textContent = item.title;
    const isMusic = item.tmdbId === -1;
    const isCourse = item.tmdbId === -2;
    const imgContainer = document.getElementById('det-img-container');
    imgContainer.className = `detail-img ${isCourse ? 'course-detail' : ''}`;

    if (isMusic) {
        imgContainer.innerHTML = generateMusicArt(item);
        document.getElementById('det-tagline').textContent = item.artist;
        document.getElementById('det-desc').textContent = `Featured in "${item.album || 'Single'}".`;
        document.getElementById('det-meta').innerHTML = `<span>${item.releaseYear}</span> <span class="acoustic-badge">${Math.round(item.tempo)} BPM</span>`;
    } else if (isCourse) {
        imgContainer.innerHTML = generateCoursePoster(item);
        document.getElementById('det-tagline').textContent = `Instructor: ${item.artist}`;
        document.getElementById('det-desc').textContent = `A top-rated lesson from ${item.album}. Category: ${item.category}`;
        document.getElementById('det-meta').innerHTML = `<span>Rating: ${item.rating} ★</span> <span class="acoustic-badge">${item.category}</span>`;
    } else {
        let meta = cache[item.tmdbId];
        if (!meta && item.tmdbId > 0) {
            // Show placeholder while fetching
            imgContainer.classList.add('skeleton');
            document.getElementById('det-desc').textContent = "Inkpick is sketching the details...";
            const res = await fetch(`/api/v1/tmdb/movie/${item.tmdbId}`);
            meta = await res.json();
            cache[item.tmdbId] = meta;
            pruneCache();
        }
        meta = meta || {};
        imgContainer.innerHTML = meta.poster_path ? `<img src="${TMDB_POSTER + meta.poster_path}">` : generateMovieSketch(item);
        document.getElementById('det-tagline').textContent = meta.tagline || "";
        document.getElementById('det-desc').textContent = meta.overview || "";
        document.getElementById('det-meta').innerHTML = `<span>${meta.release_date?.split('-')[0] || ''}</span> <span>${meta.runtime ? meta.runtime + 'm' : ''}</span>`;
    }

    const playLink = document.getElementById('det-play-link');
    const playText = document.getElementById('det-play-text');
    if (playLink && playText) {
        if (isMusic && item.spotifyId) {
            playLink.href = `https://open.spotify.com/track/${item.spotifyId}`;
            playText.textContent = "Play on Spotify";
            playLink.style.display = "inline-flex";
        } else if (isCourse && item.url) {
            playLink.href = item.url;
            playText.textContent = `Start on ${item.album}`;
            playLink.style.display = "inline-flex";
        } else if (!isMusic && !isCourse && item.tmdbId > 0) {
            playLink.href = `https://www.themoviedb.org/movie/${item.tmdbId}`;
            playText.textContent = "Experience on TMDB";
            playLink.style.display = "inline-flex";
        } else {
            playLink.style.display = "none";
        }
    }

    if (typeof lucide !== 'undefined') lucide.createIcons();
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
        pruneCache();
    } catch (err) { }
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
    return function () { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}
function generateScribblePath(rng, w, h) {
    const pts = [];
    for (let i = 0; i < 5; i++) pts.push(`${Math.floor(rng() * w)},${Math.floor(rng() * h)}`);
    return `M ${pts.join(' L ')} Z`;
}
function generateMasterpieceSketch(item, mode = 'music') {
    const seed = (item.title || 'Unknown') + (item.artist || item.releaseYear || '');
    const rng = seedRandom(seed);
    const paperType = rng() > 0.5 ? 'dot-paper' : 'graph-paper';
    const paths = [generateScribblePath(rng, 300, 450), generateScribblePath(rng, 300, 450)];
    const subText = mode === 'music' ? (item.artist || '') : (item.releaseYear || 'Cinema');
    return `<div class="sketch-canvas ${paperType}"><svg class="sketch-svg" viewBox="0 0 300 450"><path d="${paths[0]}" stroke-width="1.5" opacity="0.1" /><path d="${paths[1]}" stroke-width="1" opacity="0.05" /></svg><div class="sketch-hero-text">${item.title}</div><div class="sketch-sub-text">${subText}</div></div>`;
}

function generateMusicArt(item) { return generateMasterpieceSketch(item, 'music'); }
function generateMovieSketch(item) { return generateMasterpieceSketch(item, 'movie'); }

// ── O7: Category-based fallbacks, no Microlink ──────
function generateCoursePoster(item) {
    const cat = (item.category || 'default').toLowerCase();
    const fallback = COURSE_FALLBACKS[cat] || COURSE_FALLBACKS['default'];

    // YouTube thumbnail
    let videoId = '';
    if (item.url) {
        if (item.url.includes('youtube.com/watch?v=')) videoId = item.url.split('v=')[1].split('&')[0];
        else if (item.url.includes('youtu.be/')) videoId = item.url.split('/').pop();
    }
    if (videoId) {
        return `<img src="https://img.youtube.com/vi/${videoId}/hqdefault.jpg" class="loaded course-poster" alt="YouTube" style="width:100%;height:100%;object-fit:cover;" onerror="this.src='${fallback}'">`;
    }

    return `<img src="${fallback}" class="loaded course-poster" loading="lazy" alt="Course" style="width:100%;height:100%;object-fit:cover;">`;
}

/**
 * MASCOT ENGINE — "Real Walking"
 */
const sketchyQuotes = [
    "Searching for a masterpiece? 🖋️",
    "Did you know? 'DDLJ' is the longest-running film! 🍿",
    "Listening to Bolly-beats today? 🎸",
    "I've sketched 180,000 items so far!",
    "That Hero Card looks stunning, doesn't it?",
    "Need a recommendation? Try 'Sci-Fi'!",
    "I'm feeling wobbly today! 🤖"
];

function initMascot() {
    const mascot = document.getElementById('sketchy-mascot');
    if (!mascot) return;

    setInterval(() => {
        if (!mascot.classList.contains('active')) {
            const text = document.getElementById('sketchy-text');
            if (text) text.textContent = sketchyQuotes[Math.floor(Math.random() * sketchyQuotes.length)];
        }
    }, 10000);

    setTimeout(() => moveMascotTo('at-logo'), 1000);

    setInterval(() => {
        if (!mascot.classList.contains('active')) {
            const spots = ['at-logo', 'at-navbar', 'at-hero'];
            moveMascotTo(spots[Math.floor(Math.random() * spots.length)]);
        }
    }, 45000);
}

function moveMascotTo(state) {
    const mascot = document.getElementById('sketchy-mascot');
    const model = document.getElementById('sketchy-3d');
    if (!mascot || !model) return;

    if (state === 'at-logo') mascot.classList.add('facing-left');
    else mascot.classList.remove('facing-left');

    model.setAttribute('animation-name', 'Walking');
    mascot.classList.add('walking-bob');

    const states = ['at-navbar', 'at-hero', 'at-logo'];
    states.forEach(s => mascot.classList.remove(s));
    mascot.classList.add(state);

    const onArrival = () => {
        mascot.classList.remove('walking-bob');
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

function triggerSketchy3D(customMessage = null, customAnim = null) {
    const mascot = document.getElementById('sketchy-mascot');
    const model = document.getElementById('sketchy-3d');
    const text = document.getElementById('sketchy-text');
    if (!mascot || !model || !text) return;

    mascot.classList.add('active');

    let behavior;
    if (customMessage) {
        behavior = { anim: customAnim || "Wave", text: customMessage };
    } else {
        const behaviors = [
            { anim: "Jump", text: "Boing! Searching... 🚀" },
            { anim: "ThumbsUp", text: "Great choice! 👍" },
            { anim: "Dance", text: "Let's celebrate! 🕺" }
        ];
        behavior = behaviors[Math.floor(Math.random() * behaviors.length)];
    }

    model.setAttribute('animation-name', behavior.anim);
    text.innerHTML = behavior.text;

    const locations = ['at-navbar', 'at-hero', 'at-logo'];
    setTimeout(() => moveMascotTo(locations[Math.floor(Math.random() * locations.length)]), 1500);

    setTimeout(() => { mascot.classList.remove('active'); }, customMessage ? 6000 : 4000);
}
