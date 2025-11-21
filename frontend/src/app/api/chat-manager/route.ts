// src/app/api/chat-manager/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { db, schema } from '@/lib/db';
import { cookies } from 'next/headers';
import { listChats, deleteChat } from '@/app/util/chat-store';

export async function GET() {
  try {
    const cookieStore = await cookies();
    const cookieId = cookieStore.get('sid')?.value;
    
    if (!cookieId) {
      return NextResponse.json({ chats: [] });
    }

    const chats = await listChats(cookieId);
    return NextResponse.json({ chats });
  } catch (error) {
    console.error('Failed to fetch chats:', error);
    return NextResponse.json({ error: 'Failed to fetch chats' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
     const cookieStore = await cookies();
    const cookieId = cookieStore.get('sid')?.value;
    
    if (!cookieId) {
      return NextResponse.json({ error: 'No session found' }, { status: 401 });
    }
    
    const newChatId = crypto.randomUUID();
    
    await db.insert(schema.chats).values({
      id: newChatId,
      cookieId: cookieId,
      title: 'New Chat',
    });
    
    const newChat = {
      id: newChatId,
      title: 'New Chat',
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    
    return NextResponse.json(newChat);
  } catch (error) {
    console.error('Failed to create chat:', error);
    return NextResponse.json({ error: 'Failed to create chat' }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const chatId = searchParams.get('id');
    
    if (!chatId) {
      return NextResponse.json({ error: 'Chat ID is required' }, { status: 400 });
    }
    
    await deleteChat(chatId);
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Failed to delete chat:', error);
    return NextResponse.json({ error: 'Failed to delete chat' }, { status: 500 });
  }
}
