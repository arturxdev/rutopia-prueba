"use client";

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Message } from '@/types';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatPanelProps {
    messages: Message[];
    isLoading: boolean;
    toolStatus: string | null;
    isConnected: boolean;
    onSendMessage: (message: string) => void;
}

export function ChatPanel({
    messages,
    isLoading,
    toolStatus,
    isConnected,
    onSendMessage
}: ChatPanelProps) {
    const [input, setInput] = useState('');
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (input.trim() && !isLoading) {
            onSendMessage(input);
            setInput('');
        }
    };

    return (
        <div className="flex flex-col h-full bg-white">
            {/* Header */}
            <div className="p-4 border-b flex items-center justify-between">
                <div>
                    <h2 className="font-semibold text-lg">Rutopia Chat</h2>
                    <p className="text-sm text-gray-500">Descubre experiencias únicas en México</p>
                </div>
                <Badge variant={isConnected ? "default" : "destructive"}>
                    {isConnected ? "Conectado" : "Desconectado"}
                </Badge>
            </div>

            {/* Messages */}
            <ScrollArea className="h-0 flex-1 p-4" ref={scrollRef}>
                <div className="space-y-4">
                    {/* Mensaje de bienvenida */}
                    {messages.length === 0 && (
                        <div className="text-center py-8">
                            <h3 className="text-lg font-medium text-gray-700 mb-2">
                                ¡Hola! 👋 Soy tu asistente de viajes
                            </h3>
                            <p className="text-gray-500 mb-4">
                                Pregúntame sobre experiencias en México: cenotes, tours culturales, aventuras y más.
                            </p>
                            <div className="flex flex-wrap gap-2 justify-center">
                                {[
                                    "Cenotes cerca de Tulum para familia",
                                    "Experiencias culturales en Mérida",
                                    "Aventuras en la selva de Chiapas"
                                ].map((suggestion) => (
                                    <Button
                                        key={suggestion}
                                        variant="outline"
                                        size="sm"
                                        onClick={() => onSendMessage(suggestion)}
                                    >
                                        {suggestion}
                                    </Button>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Mensajes */}
                    {messages.map((message) => (
                        <div key={message.id}>
                            <MessageBubble message={message} />
                        </div>
                    ))}

                    {/* Status de herramienta */}
                    {toolStatus && (
                        <div className="flex items-center gap-2 text-gray-500 text-sm">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            {toolStatus}
                        </div>
                    )}
                </div>
            </ScrollArea>

            {/* Input */}
            <form onSubmit={handleSubmit} className="p-4 border-t">
                <div className="flex gap-2">
                    <Input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="¿Qué experiencia buscas?"
                        disabled={isLoading || !isConnected}
                        className="flex-1"
                    />
                    <Button
                        type="submit"
                        disabled={isLoading || !input.trim() || !isConnected}
                    >
                        {isLoading ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Send className="h-4 w-4" />
                        )}
                    </Button>
                </div>
            </form>
        </div>
    );
}

// Componente para cada mensaje
function MessageBubble({
    message
}: {
    message: Message;
}) {
    const isUser = message.role === 'user';

    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} ${isUser ? 'pr-2' : 'pl-2'}`}>
            <div className={`max-w-[85%] ${isUser ? 'order-1' : 'order-2'}`}>
                <div
                    className={`rounded-2xl px-4 py-3 ${isUser
                            ? 'bg-blue-500 text-white rounded-tr-sm'
                            : 'bg-gray-100 text-gray-800 rounded-tl-sm'
                        }`}
                >
                    <div className={`prose prose-sm max-w-none ${isUser ? 'prose-invert' : ''}`}>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                        </ReactMarkdown>
                    </div>
                </div>
            </div>
        </div>
    );
}