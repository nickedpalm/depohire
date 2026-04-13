// Quick test: try to fetch Listmonk from CF Worker context
export async function onRequestGet({ env }) {
  const url = env.LISTMONK_URL || 'https://mail.firestick.io';
  const user = env.LISTMONK_USER || 'none';
  const pass = env.LISTMONK_PASS || 'none';
  const listId = env.LISTMONK_LIST_ID || '0';
  
  const result = { url, user, listId: parseInt(listId), passSet: pass !== 'none' && pass.length > 0 };
  
  try {
    const auth = btoa(user + ':' + pass);
    const resp = await fetch(url + '/api/lists?page=1&per_page=3', {
      headers: { 'Authorization': 'Basic ' + auth }
    });
    result.listmonkStatus = resp.status;
    result.listmonkBody = await resp.text();
  } catch (err) {
    result.listmonkError = err.message || String(err);
  }
  
  return new Response(JSON.stringify(result, null, 2), {
    headers: { 'Content-Type': 'application/json' }
  });
}
