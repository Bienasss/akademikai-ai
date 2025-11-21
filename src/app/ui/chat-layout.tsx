// src/app/ui/chat-layout.tsx
'use client';

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import ChatSidebar from '@/app/ui/chat-sidebar';

interface Chat {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount?: number;
}

interface ChatLayoutProps {
  children: React.ReactNode;
}

export default function ChatLayout({ children }: ChatLayoutProps) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const chatId = pathname.includes('/api/chat/') ? pathname.split('/api/chat/')[1] : null;
  const isChatRoute = pathname.startsWith('/api/chat/');

  useEffect(() => {
    loadChats();
  }, []);

  useEffect(() => {
    if (isChatRoute) {
      loadChats();
    }
  }, [pathname]);

  useEffect(() => {
    const handleFocus = () => {
      loadChats();
    };
    
    window.addEventListener('focus', handleFocus);
    return () => window.removeEventListener('focus', handleFocus);
  }, []);

  const loadChats = async () => {
    try {
      const response = await fetch('/api/chat-manager');
      if (response.ok) {
        const data = await response.json();
        setChats(data.chats || []);
      }
    } catch (error) {
      console.error('Failed to load chats:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    try {
      const response = await fetch('/api/chat-manager', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'New Chat' }),
      });
      
      if (response.ok) {
        const newChat = await response.json();
        await loadChats();
        router.push(`/api/chat/${newChat.id}`);
      }
    } catch (error) {
      console.error('Failed to create chat:', error);
    }
  };

  const handleChatSelect = (selectedChatId: string) => {
    router.push(`/api/chat/${selectedChatId}`);
    setIsSidebarOpen(false); 
  };

  const handleDeleteChat = async (chatIdToDelete: string) => {
    try {
      const response = await fetch(`/api/chat-manager?id=${chatIdToDelete}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        await loadChats();
        if (chatIdToDelete === chatId) {
          const remainingChats = chats.filter(chat => chat.id !== chatIdToDelete);
          if (remainingChats.length > 0) {
            router.push(`/api/chat/${remainingChats[0].id}`);
          } else {
            handleNewChat();
          }
        }
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
    }
  };

  if (!isChatRoute) {
    return <>{children}</>;
  }

  if (isLoading) {
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="w-64 bg-white border-r border-gray-200 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}
      
      <div className={`
        fixed lg:static inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 ease-in-out
        ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0 lg:flex lg:flex-col
      `}>
        <ChatSidebar
          chats={chats}
          currentChatId={chatId || ''}
          onChatSelect={handleChatSelect}
          onNewChat={handleNewChat}
          onDeleteChat={handleDeleteChat}
        />
      </div>
      
      <div className="flex-1 flex flex-col lg:ml-0 min-h-0">
        <div className="lg:hidden bg-white border-b border-gray-200 p-4 flex items-center justify-between flex-shrink-0">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <h1 className="text-lg font-semibold text-gray-900">Chat</h1>
          <div className="w-10" />
        </div>
        
        <div className="flex-1 overflow-hidden min-h-0">
          {children}
        </div>
      </div>
    </div>
  );
}
