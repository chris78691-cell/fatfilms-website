// Lightweight TMDB proxy for the suggest autocomplete. Accepts ?q=<query>
// and returns the top few movie + TV matches so the browser can show them
// alongside site films and leaderboard entries without exposing the TMDB
// token. Uses the same ranking (quality filter + vote_count * popularity)
// as /api/suggest so the suggestions match what would land on the leaderboard.

const TMDB_BASE = 'https://api.themoviedb.org/3';
const QUALITY_VOTE_COUNT = 50;
const MAX_RESULTS = 8;

async function searchTmdb(endpoint, query) {
  const url = `${TMDB_BASE}${endpoint}?query=${encodeURIComponent(query)}&include_adult=false&language=en-US&page=1`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${process.env.TMDB_TOKEN}`,
      Accept: 'application/json',
    },
  });
  if (!res.ok) throw new Error(`TMDB ${endpoint} ${res.status}`);
  return res.json();
}

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const q = (req.query.q || '').toString().trim();
  if (!q || q.length < 2) {
    return res.status(200).json({ results: [] });
  }
  if (q.length > 80) {
    return res.status(400).json({ error: 'Query too long.' });
  }

  try {
    const [movieJson, tvJson] = await Promise.all([
      searchTmdb('/search/movie', q),
      searchTmdb('/search/tv', q),
    ]);
    const combined = [
      ...(movieJson.results || []).map(r => ({ ...r, media_type: 'movie' })),
      ...(tvJson.results || []).map(r => ({ ...r, media_type: 'tv' })),
    ].filter(r => r.title || r.name);

    // Quality bar first; if everything gets filtered out (new / obscure
    // titles) fall back to the unfiltered pool so nothing is unreachable.
    const quality = combined.filter(r => (r.vote_count || 0) >= QUALITY_VOTE_COUNT);
    const pool = quality.length > 0 ? quality : combined;

    const results = pool
      .map(r => ({
        tmdb_id: r.id,
        media_type: r.media_type,
        title: r.title || r.name,
        year: (r.release_date || r.first_air_date || '').slice(0, 4),
        poster_url: r.poster_path ? `https://image.tmdb.org/t/p/w92${r.poster_path}` : null,
        score: (r.vote_count || 0) * (r.popularity || 0),
      }))
      .sort((a, b) => b.score - a.score)
      .slice(0, MAX_RESULTS)
      .map(({ score, ...rest }) => rest); // drop internal score from the response

    // Edge cache popular queries for a minute so typing doesn't hammer TMDB.
    res.setHeader('Cache-Control', 's-maxage=60, stale-while-revalidate=300');
    return res.status(200).json({ results });
  } catch (e) {
    console.error('films-search error:', e);
    return res.status(502).json({ error: "Couldn't reach TMDB." });
  }
}
