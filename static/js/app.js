/**
 * Suggesto — Hand-Drawn Discovery Client
 * Logic for search, recommendation, and UI interactions.
 */

let currentTab = 'movies';
const TMDB_POSTER = 'https://image.tmdb.org/t/p/w500';
const cache = {};

const input = document.getElementById('query-input');
const grid = document.getElementById('discovery-results');
const header = document.getElementById('grid-header');
const detailView = document.getElementById('detail-view');

/**
 * Initialize Lucide Icons and fetch default discovery
 */
window.onload = () => {
    if (typeof lucide !== "undefined") {
        lucide.createIcons();
    }
    handleDiscover('Inception');
};

/**
 * Event Listeners
 */
input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') handleDiscover(input.value.trim());
});

/**
 * UI State Management
 */
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
    
    if (tab === 'movies') {
        handleDiscover('Inception');
    } else {
        const title = tab === 'songs' ? 'Melody Drafts' : 'Knowledge Sketch';
        grid.innerHTML = `
            <div style="padding: 40px; text-align: center; font-family: var(--font-header); font-size: 1.5rem;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">✍️</div>
                "${title}" section is currently being sketched...
            </div>`;
    }
}

/**
 * API Interactions
 */
async function handleDiscover(q) {
    if (q.length < 2 || currentTab !== 'movies') return;
    
    const searchBox = document.querySelector('.search-box');
    if (searchBox) searchBox.style.borderColor = "var(--accent)";
    
    try {
        const res = await fetch(`/api/v1/movies/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        renderItems(data.results || []);
    } catch (err) {
        console.error("Discovery error:", err);
    } finally {
        if (searchBox) searchBox.style.borderColor = "var(--foreground)";
    }
}

/**
 * Rendering Logic
 */
function renderItems(items) {
    if (!grid) return;
    grid.innerHTML = '';
    
    items.forEach((item, i) => {
        const card = document.createElement('div');
        card.className = 'card';
        
        // Random rotation for wobbly hand-drawn effect
        const rot = (Math.random() * 4 - 2).toFixed(1);
        card.style.setProperty('--rand-rot', `${rot}deg`);
        card.style.animationDelay = `${i * 0.05}s`;
        card.onclick = () => selectItem(item);
        
        const matchPct = item.similarity ? `${Math.round(item.similarity * 100)}% Match` : '';

        card.innerHTML = `
            <div class="match-label">${matchPct || 'Picked'}</div>
            <div class="card-img">
                <img src="" id="img-${item.tmdbId}" class="skeleton">
            </div>
            <div class="card-title">${item.title}</div>
            <div class="card-meta-line">
                <span class="rating" id="rate-${item.tmdbId}"></span>
                <span style="opacity: 0.3">|</span>
                <span>${item.releaseYear || ''}</span>
                <span style="opacity: 0.3">|</span>
                <span id="genre-${item.tmdbId}"></span>
            </div>
        `;

        grid.appendChild(card);
        
        // If the backend already included cached metadata, use it immediately!
        if (item.cached) {
            updateCard(item.tmdbId, card, item.cached);
        } else {
            fetchMeta(item.tmdbId, card);
        }
    });
}

async function fetchMeta(tid, cardEl) {
    if (!tid || tid <= 0) return;
    if (cache[tid]) {
        updateCard(tid, cardEl, cache[tid]);
        return;
    }
    
    try {
        const res = await fetch(`/api/v1/tmdb/movie/${tid}`);
        const data = await res.json();
        cache[tid] = data;
        updateCard(tid, cardEl, data);
    } catch (err) {
        console.error(`Metadata fetch failed for ${tid}:`, err);
    }
}

function updateCard(tid, cardEl, data) {
    const img = cardEl.querySelector(`#img-${tid}`);
    if (img) {
        img.src = data.poster_path ? TMDB_POSTER + data.poster_path : '';
        img.onload = () => img.classList.add('loaded');
        img.classList.remove('skeleton');
    }

    const rate = cardEl.querySelector(`#rate-${tid}`);
    if (rate && data.vote_average) {
        rate.innerHTML = `
            <i data-lucide="star" style="width: 14px; fill: var(--accent); color: var(--accent);"></i>
            ${data.vote_average.toFixed(1)}`;
    }
    
    const genre = cardEl.querySelector(`#genre-${tid}`);
    if (genre && data.genres) {
        genre.textContent = data.genres.slice(0, 1).map(g => g.name).join(', ');
    }
    
    if (typeof lucide !== "undefined") {
        lucide.createIcons({ attrs: { 'stroke-width': 3 } });
    }
}

async function selectItem(item) {
    if (!detailView) return;
    
    detailView.style.display = 'block';
    document.getElementById('det-title').textContent = item.title;
    document.getElementById('det-desc').textContent = "Penciling in details...";
    document.getElementById('det-tagline').textContent = "";
    document.getElementById('det-meta').innerHTML = "";
    
    window.scrollTo({ top: 0, behavior: 'smooth' });

    try {
        const meta = cache[item.tmdbId] || await (await fetch(`/api/v1/tmdb/movie/${item.tmdbId}`)).json();
        cache[item.tmdbId] = meta;
        
        document.getElementById('det-tagline').textContent = meta.tagline ? `"${meta.tagline}"` : "";
        document.getElementById('det-desc').textContent = meta.overview;
        
        const detImg = document.getElementById('det-img');
        if (detImg) {
            detImg.src = meta.poster_path ? TMDB_POSTER + meta.poster_path : '';
        }
        
        const genres = meta.genres.map(g => g.name).join(' • ');
        const year = meta.release_date ? meta.release_date.split('-')[0] : '';
        const runtime = meta.runtime ? `${meta.runtime} min` : '';
        
        document.getElementById('det-meta').innerHTML = `
            <span>${year}</span>
            <span style="color: var(--secondary)">●</span>
            <span>${genres}</span>
            <span style="color: var(--secondary)">●</span>
            <span>${runtime}</span>
            <span style="color: var(--secondary)">●</span>
            <span class="rating">
                <i data-lucide="star" style="width: 18px; fill: var(--accent); color: var(--accent);"></i>
                ${meta.vote_average.toFixed(1)}
            </span>
        `;

        if (typeof lucide !== "undefined") {
            lucide.createIcons();
        }

        // Recommendations
        const res = await fetch(`/api/v1/recommend/movies/${item.movieId}?limit=10`);
        const data = await res.json();
        if (header) {
            header.textContent = "Recommended Revisions (Related Sketches):";
        }
        renderItems(data.recommendations);
        
    } catch (err) {
        console.error("Detail view load error:", err);
    }
}
