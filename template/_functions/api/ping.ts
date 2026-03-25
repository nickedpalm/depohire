// Minimal test function - no imports
export const onRequestGet: PagesFunction = async () => {
  return new Response(JSON.stringify({ pong: true, ts: Date.now() }), {
    headers: { 'Content-Type': 'application/json' },
  });
};
