// src/app/api/chat/route.ts
import {
  convertToModelMessages,
  streamText,
  UIMessage,
  validateUIMessages,
  createIdGenerator,
  stepCountIs,
} from 'ai';
//import { z } from 'zod';
import { clearAllMessages, loadChat, saveChat, generateChatTitle } from '@/app/util/chat-store';
import { openai } from '@ai-sdk/openai';
import { after } from 'next/server';
import { createResumableStreamContext } from 'resumable-stream'
import { getMCPClient } from '@/lib/tools';


export async function POST(req: Request) {
  const { message, id }: { message: UIMessage | undefined; id: string; } = await req.json();  

  const { messages: previousMessages } = await loadChat(id);
  
  const messages = [...previousMessages, message!];

  const mcpClient = await getMCPClient();
  const mcpTools = await mcpClient.tools();

  const validatedMessages = await validateUIMessages({
    messages,
  });

  saveChat({ chatId: id, messages, streamId: null });

  const result = streamText({
    model: openai('gpt-4o-mini'),
    messages: convertToModelMessages(validatedMessages),
    tools: mcpTools,
    stopWhen: stepCountIs(5),
  });

  return result.toUIMessageStreamResponse({
    originalMessages: messages,
    generateMessageId: createIdGenerator({
      prefix: 'msg',
      size: 16,
    }),
    onFinish: ({ messages }) => {
     saveChat({ chatId: id, messages, streamId: null });
     
     const userMessages = messages.filter(m => m.role === 'user');
     if (userMessages.length === 1) { 
       generateChatTitle(id);
     }
    },
    async consumeSseStream({ stream }) {
      const streamId = crypto.randomUUID();

      const streamContext = createResumableStreamContext({ waitUntil: after });
      await streamContext.createNewResumableStream(streamId, () => stream);

      saveChat({ chatId: id, messages: [], streamId: streamId });
    },
  });
}
