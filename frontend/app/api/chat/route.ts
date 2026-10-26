import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  let step = "Starting request";
  
  try {
    step = "Reading incoming browser request";
    const body = await req.json();
    
    step = "Extracting variables";
    const rawMessages = body.messages || [];
    const sessionToken = body.session_token;

    if (!sessionToken) {
      return NextResponse.json(
        { reply: "Session token is missing from the frontend." },
        { status: 400 }
      );
    }

    step = "Sanitizing messages";
    const sanitizedMessages = rawMessages
      .filter((m: any) => 
        m.content !== 'Unable to reach the transit AI backend.' && 
        !m.content.startsWith('Backend validation error') &&
        !m.content.startsWith('Connection error') &&
        !m.content.startsWith('Crashed at step')
      )
      .map((m: any) => ({
        role: m.role === 'user' ? 'user' : 'assistant',
        content: String(m.content || ''),
      }));

    step = "Sending fetch request to FastAPI";
    const backendUrl = process.env.BACKEND_URL || 'http://backend:8000';
    const response = await fetch(`${backendUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        session_token: sessionToken,
        messages: sanitizedMessages 
      }),
    });

    step = "Checking FastAPI response status";
    if (!response.ok) {
      step = "Reading FastAPI error body";
      const rawText = await response.text(); 
      return NextResponse.json(
        { reply: `Backend validation error (HTTP ${response.status}): ${rawText}` },
        { status: response.status }
      );
    }

    step = "Reading FastAPI success body";
    const data = await response.json();
    
    step = "Returning response to browser";
    return NextResponse.json({ reply: data.reply });
    
  } catch (error: any) {
    console.error(`Crashed at step [${step}]:`, error);
    return NextResponse.json(
      { reply: `Crashed at step [${step}]: ${error.message}` },
      { status: 500 }
    );
  }
}