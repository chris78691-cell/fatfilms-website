import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_ANON_KEY
);

export default async function handler(req, res) {
  if (req.method !== 'GET') {
    res.setHeader('Allow', 'GET');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { data, error } = await supabase
    .from('like_counts')
    .select('film_slug, count');

  if (error) {
    console.error('likes endpoint error:', error);
    return res.status(500).json({ error: 'Database error.' });
  }

  const map = {};
  (data || []).forEach(row => { map[row.film_slug] = row.count; });

  // Short TTL so a like placed by one user becomes visible to everyone else
  // within ~5s. stale-while-revalidate keeps the UI snappy while the edge
  // quietly refreshes in the background.
  res.setHeader('Cache-Control', 's-maxage=5, stale-while-revalidate=30');
  return res.status(200).json(map);
}
