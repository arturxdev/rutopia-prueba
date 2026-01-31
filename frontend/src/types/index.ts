export interface Experience {
    id: string;
    name: string;
    summary: string;
    lat: number;
    lon: number;
    duration: string | null;
    location: string;
    destination: string | null;
    highlights: string[];
    type: string | null;
    intensity: string | null;
    family_friendly: boolean | null;
    includes_food: boolean | null;
    includes_transport: boolean | null;
    similarity?: number | null;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    experiences?: Experience[];
}

export type WSMessageType =
    | { type: 'message'; content: string }
    | { type: 'thinking_start' }
    | { type: 'tool_start'; message: string }
    | { type: 'tool_end' }
    | { type: 'experiences'; data: Experience[] }
    | { type: 'done' }
    | { type: 'error'; message: string };