import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const rawMessages = body.messages || [];

    // Filter out previous frontend failure messages and strip extra fields (like `id`)
    const sanitizedMessages = rawMessages
      .filter((m: any) => m.content !== 'Unable to reach the transit AI backend.')
      .map((m: any) => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: String(m.content || ''),
      }));

    const backendUrl = process.env.BACKEND_URL || 'http://backend:8000';

    const response = await fetch(`${backendUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ messages: sanitizedMessages }),
    });

    if (!response.ok) {
      const errDetail = await response.text();
      console.error(`FastAPI returned status ${response.status}:`, errDetail);
      return NextResponse.json(
        { reply: `Backend error (${response.status}): ${errDetail}` },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json({ reply: data.reply });
  } catch (error: any) {
    console.error('Bridge error:', error);
    return NextResponse.json(
      { reply: `Connection error: ${error.message}` },
      { status: 500 }
    );
  }
}