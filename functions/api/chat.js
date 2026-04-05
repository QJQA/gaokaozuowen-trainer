export async function onRequestPost(context) {
  try {
    const data = await context.request.json();
    const { model = 'kimi-k2.5', max_tokens = 2000, messages = [] } = data;
    const api_key = context.env.KIMI_API_KEY || '';

    const response = await fetch('https://api.moonshot.cn/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${api_key}`
      },
      body: JSON.stringify({ model, max_tokens, messages })
    });

    const result = await response.json();
    return new Response(JSON.stringify(result), {
      status: response.status,
      headers: { 'Content-Type': 'application/json' }
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: { message: e.message } }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
