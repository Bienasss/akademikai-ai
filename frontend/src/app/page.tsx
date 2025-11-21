// src/app/page.tsx
import { redirect } from 'next/navigation';
import { createChat } from '@/app/util/chat-store';
import { cookies } from 'next/headers';

export default async function Page() {
  const cookieStore = await cookies();
  const cookieId = cookieStore.get('sid')?.value;
  
  if (!cookieId) {
    throw new Error('No session cookie found'); // Fails only if middleware is not working
  }
  
  const chatId = await createChat(cookieId);
  redirect(`/api/chat/${chatId}`);
}