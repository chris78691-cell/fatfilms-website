import { createClient } from '@supabase/supabase-js';
import crypto from 'crypto';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);

function getClientIp(req) {
  const fwd = req.headers['x-forwarded-for'];
  if (typeof fwd === 'string' && fwd.length > 0) return fwd.split(',')[0].trim();
  return req.headers['x-real-ip'] || req.socket?.remoteAddress || 'unknown';
}

function hashIp(ip) {
  return crypto.createHash('sha256').update(ip).digest('hex');
}

async function readCount(slug) {
  const { data, error } = await supabase
    .from('like_counts')
    .select('count')
    .eq('film_slug', slug)
    .maybeSingle();
  if (error) throw error;
  return data?.count ?? 0;
}

async function setCount(slug, count) {
  const { data, error } = await supabase
    .from('like_counts')
    .select('film_slug')
    .eq('film_slug', slug)
    .maybeSingle();
  if (error) throw error;
  if (data) {
    const { error: upErr } = await supabase
      .from('like_counts')
      .update({ count })
      .eq('film_slug', slug);
    if (upErr) throw upErr;
  } else {
    const { error: insErr } = await supabase
      .from('like_counts')
      .insert({ film_slug: slug, count });
    if (insErr) throw insErr;
  }
}

function safeJson(s) { try { return JSON.parse(s); } catch { return {}; } }

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const body = typeof req.body === 'string' ? safeJson(req.body) : (req.body || {});
  const slug = typeof body.film_slug === 'string' ? body.film_slug.trim() : '';
  const action = body.action;

  if (!slug || !/^[a-z0-9-]+$/.test(slug) || slug.length > 80) {
    return res.status(400).json({ error: 'Invalid film_slug.' });
  }
  if (action !== 'like' && action !== 'unlike') {
    return res.status(400).json({ error: 'action must be "like" or "unlike".' });
  }

  const ipHash = hashIp(getClientIp(req));

  try {
    if (action === 'like') {
      // Has this hash already liked this film?
      const { data: existing, error: selErr } = await supabase
        .from('likes')
        .select('id')
        .eq('film_slug', slug)
        .eq('ip_hash', ipHash)
        .maybeSingle();
      if (selErr) throw selErr;

      if (existing) {
        const count = await readCount(slug);
        return res.status(200).json({ success: true, already_liked: true, liked: true, count });
      }

      const { error: insErr } = await supabase
        .from('likes')
        .insert({ film_slug: slug, ip_hash: ipHash });
      if (insErr) throw insErr;

      const current = await readCount(slug);
      const next = current + 1;
      await setCount(slug, next);
      return res.status(200).json({ success: true, liked: true, count: next });
    }

    // unlike: best-effort delete; count decrements only if the delete actually removed a row.
    const { data: deleted, error: delErr } = await supabase
      .from('likes')
      .delete()
      .eq('film_slug', slug)
      .eq('ip_hash', ipHash)
      .select('id');
    if (delErr) throw delErr;

    const current = await readCount(slug);
    const next = (deleted && deleted.length > 0) ? Math.max(0, current - 1) : current;
    if (next !== current) await setCount(slug, next);
    return res.status(200).json({ success: true, liked: false, count: next });
  } catch (e) {
    console.error('like endpoint error:', e);
    return res.status(500).json({ error: 'Database error.' });
  }
}
