import {
  convertToModelMessages,
  streamText,
  UIMessage,
  validateUIMessages,
  createIdGenerator,
  stepCountIs,
} from 'ai';
import { clearAllMessages, loadChat, saveChat, generateChatTitle } from '@/app/util/chat-store';
import { openai } from '@ai-sdk/openai';
import { after } from 'next/server';
import { createResumableStreamContext } from 'resumable-stream'
import { getMCPClient } from '@/lib/tools';

const PYTHON_BACKEND_URL = process.env.PYTHON_BACKEND_URL || 'http://localhost:8000';

async function getRAGContext(query: string): Promise<{ context: string; sources: any[] } | null> {
  try {
    const response = await fetch(`${PYTHON_BACKEND_URL}/api/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ query, top_k: 5 }),
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    if (data.status === 'success' && data.context) {
      return {
        context: data.context,
        sources: data.sources || []
      };
    }
    return null;
  } catch (error) {
    console.error('RAG context error:', error);
    return null;
  }
}

export async function POST(req: Request) {
  const { message, id }: { message: UIMessage | undefined; id: string; } = await req.json();  

  const { messages: previousMessages } = await loadChat(id);
  
  const messages = [...previousMessages, message!];

  let enhancedMessages = messages;
  
  if (message && message.role === 'user' && typeof message.content === 'string') {
    const ragContext = await getRAGContext(message.content);
    
    if (ragContext && ragContext.context) {
      const systemMessage: UIMessage = {
        id: 'rag-context',
        role: 'system',
        content: `Relevant document context:\n\n${ragContext.context}\n\nUse this context to answer the user's question. Cite sources when referencing specific information. If the context doesn't contain relevant information, say so.`
      };
      
      enhancedMessages = [systemMessage, ...messages];
    }
  }

  const mcpClient = await getMCPClient();
  const mcpTools = await mcpClient.tools();

  const validatedMessages = await validateUIMessages({
    messages: enhancedMessages,
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
