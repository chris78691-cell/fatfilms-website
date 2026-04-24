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

  res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=60');
  return res.status(200).json(map);
}
