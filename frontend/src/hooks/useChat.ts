"use client";

import { useState, useCallback, useRef, useEffect } from 'react';
import { Experience, Message, WSMessageType } from '@/types';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/chat';

export function useChat() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isConnected, setIsConnected] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [experiences, setExperiences] = useState<Experience[]>([]);
    const [toolStatus, setToolStatus] = useState<string | null>(null);

    const wsRef = useRef<WebSocket | null>(null);
    const sessionIdRef = useRef<string>(`session-${Date.now()}`);
    const experiencesRef = useRef<Experience[]>([]);

    useEffect(() => {
        const connectWebSocket = () => {
            const ws = new WebSocket(`${WS_URL}/${sessionIdRef.current}`);

            ws.onopen = () => {
                console.log('✅ WebSocket conectado');
                setIsConnected(true);
            };

            ws.onmessage = (event) => {
                const data: WSMessageType = JSON.parse(event.data);
                console.log('Mensaje recibido:', data);

                switch (data.type) {
                    case 'message':
                        // Guardar mensaje completo directamente
                        setMessages(prev => [...prev, {
                            id: `msg-${Date.now()}`,
                            role: 'assistant',
                            content: data.content,
                            experiences: [...experiencesRef.current]
                        }]);
                        // Limpiar experiencesRef para el siguiente mensaje
                        // (setExperiences NO se limpia para mantener el mapa con las últimas experiencias)
                        experiencesRef.current = [];
                        break;

                    case 'thinking_start':
                        // Opcional: podrías mostrar un indicador de "pensando..."
                        break;

                    case 'tool_start':
                        setToolStatus(data.message);
                        break;

                    case 'tool_end':
                        setToolStatus(null);
                        break;

                    case 'experiences':
                        experiencesRef.current = data.data;
                        setExperiences(data.data);
                        break;

                    case 'done':
                        // Solo limpiar estados, NO guardar mensaje (ya se guardó en 'message')
                        setIsLoading(false);
                        break;

                    case 'error':
                        console.error('Error del servidor:', data.message);
                        setIsLoading(false);
                        setToolStatus(null);
                        break;

                    default:
                        console.warn('Evento WebSocket no manejado:', data);
                }
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                setIsConnected(false);
            };

            ws.onclose = () => {
                console.log('WebSocket desconectado');
                setIsConnected(false);
                // Reconectar después de 3 segundos
                setTimeout(connectWebSocket, 3000);
            };

            wsRef.current = ws;
        };

        connectWebSocket();

        return () => {
            wsRef.current?.close();
        };
    }, []);

    const sendMessage = useCallback((content: string) => {
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            console.error('WebSocket no conectado');
            return;
        }

        if (!content.trim()) return;

        // Agregar mensaje del usuario
        const userMessage: Message = {
            id: `msg-${Date.now()}`,
            role: 'user',
            content: content.trim()
        };

        setMessages(prev => [...prev, userMessage]);
        setIsLoading(true);
        // ✅ NO limpiar experiencias aquí
        // Las experiencias se actualizarán cuando llegue el mensaje 'experiences' del WebSocket

        // Enviar al backend
        wsRef.current.send(JSON.stringify({ content: content.trim() }));
    }, []);

    const clearChat = useCallback(() => {
        setMessages([]);
        setExperiences([]);
        experiencesRef.current = [];
    }, []);

    return {
        messages,
        isConnected,
        isLoading,
        experiences,
        toolStatus,
        sendMessage,
        clearChat
    };
}