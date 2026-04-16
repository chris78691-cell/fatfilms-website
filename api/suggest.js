import { createClient } from '@supabase/supabase-js';
import Filter from 'bad-words';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);

const filter = new Filter();

// Simple in-memory rate limit: 5 submissions per IP per hour.
// Persists across warm invocations; resets on cold start (good enough for now).
const rateLimit = new Map();
const RATE_LIMIT_MAX = 5;
const RATE_LIMIT_WINDOW_MS = 60 * 60 * 1000;

function getClientIp(req) {
  const fwd = req.headers['x-forwarded-for'];
  if (typeof fwd === 'string' && fwd.length > 0) return fwd.split(',')[0].trim();
  return req.headers['x-real-ip'] || req.socket?.remoteAddress || 'unknown';
}

const TMDB_BASE = 'https://api.themoviedb.org/3';
const QUALITY_VOTE_COUNT = 50;

async function searchTmdb(endpoint, query) {
  const url = `${TMDB_BASE}${endpoint}?query=${encodeURIComponent(query)}&include_adult=false&language=en-US&page=1`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${process.env.TMDB_TOKEN}`,
      Accept: 'application/json'
    }
  });
  if (!res.ok) throw new Error(`TMDB ${endpoint} returned ${res.status}`);
  return res.json();
}

function pickBestMatch(results) {
  const valid = (results || []).filter(r => r.title || r.name);
  if (valid.length === 0) return null;

  // Prefer results that clear a quality bar (vote_count >= 50) to strip out
  // obvious low-quality results up front.
  const quality = valid.filter(r => (r.vote_count || 0) >= QUALITY_VOTE_COUNT);
  const pool = quality.length > 0 ? quality : valid;

  // Composite score: vote_count * popularity. Heavily favours mainstream titles
  // with both high lifetime engagement AND current popularity, while still
  // letting newer trending things beat old obscure ones.
  const score = r => (r.vote_count || 0) * (r.popularity || 0);

  return pool.reduce((best, cur) => (score(cur) > score(best) ? cur : best));
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  // Rate limit per IP
  const ip = getClientIp(req);
  const now = Date.now();
  const recent = (rateLimit.get(ip) || []).filter(t => now - t < RATE_LIMIT_WINDOW_MS);
  if (recent.length >= RATE_LIMIT_MAX) {
    return res.status(429).json({ error: 'Too many submissions. Try again in a bit.' });
  }

  // Parse title
  const body = typeof req.body === 'string' ? safeJson(req.body) : (req.body || {});
  const title = typeof body.title === 'string' ? body.title.trim() : '';
  if (!title) {
    return res.status(400).json({ error: 'Please enter a film or show title.' });
  }
  if (title.length > 200) {
    return res.status(400).json({ error: 'That title is too long.' });
  }

  // Profanity filter
  try {
    if (filter.isProfane(title)) {
      return res.status(400).json({ error: 'Please keep suggestions clean.' });
    }
  } catch (_) {
    // bad-words occasionally throws on odd characters; fall through.
  }

  // Query movie and TV endpoints in parallel and merge — more control than multi-search
  let movieResults, tvResults;
  try {
    const [movieJson, tvJson] = await Promise.all([
      searchTmdb('/search/movie', title),
      searchTmdb('/search/tv', title)
    ]);
    movieResults = (movieJson.results || []).map(r => ({ ...r, media_type: 'movie' }));
    tvResults = (tvJson.results || []).map(r => ({ ...r, media_type: 'tv' }));
  } catch (e) {
    console.error('TMDB search error:', e);
    return res.status(502).json({ error: "Couldn't reach TMDB. Try again." });
  }

  const combined = [...movieResults, ...tvResults];
  const best = pickBestMatch(combined);
  if (!best) {
    return res.status(404).json({
      error: "Couldn't find that film or show, check your spelling?"
    });
  }

  const tmdbId = best.id;
  const mediaType = best.media_type;
  const canonicalTitle = best.title || best.name;
  const posterUrl = best.poster_path
    ? `https://image.tmdb.org/t/p/w200${best.poster_path}`
    : null;

  // Upsert / increment vote_count. Small race-condition window acceptable here.
  const { data: existing, error: selectErr } = await supabase
    .from('suggestions')
    .select('id, vote_count')
    .eq('tmdb_id', tmdbId)
    .maybeSingle();

  if (selectErr) {
    console.error('Supabase select error:', selectErr);
    return res.status(500).json({ error: 'Database error.' });
  }

  if (existing) {
    const { error: updateErr } = await supabase
      .from('suggestions')
      .update({ vote_count: (existing.vote_count || 0) + 1 })
      .eq('id', existing.id);
    if (updateErr) {
      console.error('Supabase update error:', updateErr);
      return res.status(500).json({ error: 'Database error.' });
    }
  } else {
    const { error: insertErr } = await supabase
      .from('suggestions')
      .insert({
        tmdb_id: tmdbId,
        media_type: mediaType,
        title: canonicalTitle,
        poster_url: posterUrl,
        vote_count: 1
      });
    if (insertErr) {
      console.error('Supabase insert error:', insertErr);
      return res.status(500).json({ error: 'Database error.' });
    }
  }

  // Record successful submission for rate limiting
  recent.push(now);
  rateLimit.set(ip, recent);

  // Fetch the refreshed top 15 so the client doesn't need a follow-up request
  const { data: leaderboard, error: lbErr } = await supabase
    .from('suggestions')
    .select('tmdb_id, title, poster_url, vote_count')
    .order('vote_count', { ascending: false })
    .limit(15);

  if (lbErr) {
    console.error('Supabase leaderboard-after-upsert error:', lbErr);
  }

  return res.status(200).json({
    success: true,
    title: canonicalTitle,
    poster_url: posterUrl,
    tmdb_id: tmdbId,
    media_type: mediaType,
    leaderboard: leaderboard || []
  });
}

function safeJson(s) {
  try { return JSON.parse(s); } catch { return {}; }
}
