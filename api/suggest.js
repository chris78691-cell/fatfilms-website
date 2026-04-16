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

function pickBestMatch(results) {
  const candidates = (results || []).filter(r =>
    (r.media_type === 'movie' || r.media_type === 'tv') && (r.title || r.name)
  );
  if (candidates.length === 0) return null;
  // TMDB orders by popularity by default; take the first valid match.
  return candidates[0];
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

  // TMDB multi-search
  let tmdbJson;
  try {
    const tmdbRes = await fetch(
      `https://api.themoviedb.org/3/search/multi?query=${encodeURIComponent(title)}&include_adult=false&language=en-US&page=1`,
      {
        headers: {
          Authorization: `Bearer ${process.env.TMDB_TOKEN}`,
          Accept: 'application/json'
        }
      }
    );
    if (!tmdbRes.ok) {
      return res.status(502).json({ error: "Couldn't reach TMDB. Try again." });
    }
    tmdbJson = await tmdbRes.json();
  } catch (e) {
    return res.status(502).json({ error: "Couldn't reach TMDB. Try again." });
  }

  const best = pickBestMatch(tmdbJson.results);
  if (!best) {
    return res.status(404).json({
      error: "Couldn't find that film or show — check your spelling?"
    });
  }

  const tmdbId = best.id;
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

  return res.status(200).json({
    success: true,
    title: canonicalTitle,
    poster_url: posterUrl,
    tmdb_id: tmdbId
  });
}

function safeJson(s) {
  try { return JSON.parse(s); } catch { return {}; }
}
