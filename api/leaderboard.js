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
    .from('suggestions')
    .select('tmdb_id, title, poster_url, vote_count')
    .order('vote_count', { ascending: false })
    .limit(20);

  if (error) {
    console.error('Supabase leaderboard error:', error);
    return res.status(500).json({ error: 'Database error.' });
  }

  // Cache briefly at the edge to cushion bursts of opens.
  res.setHeader('Cache-Control', 's-maxage=15, stale-while-revalidate=60');
  return res.status(200).json({ suggestions: data || [] });
}
