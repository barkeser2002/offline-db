import { useEffect, useRef, useState, useCallback } from 'react';

type WebSocketMessage = {
  type: string;
  [key: string]: any;
};

export function useSyncManager(roomUuid: string, user: any, videoRef: React.RefObject<HTMLVideoElement | null>) {
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [participants, setParticipants] = useState<any[]>([]);
  const [chatMessages, setChatMessages] = useState<any[]>([]);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);
  
  // Drift Correction Threshold (seconds)
  const DRIFT_THRESHOLD = 1.5;

  const triggerEmoteRain = useCallback((emote: string) => {
    // Dispatch custom event for UI to pick up
    window.dispatchEvent(new CustomEvent('emote-rain', { detail: { emote } }));
  }, []);

  const handleVideoSync = useCallback((data: any) => {
    if (!videoRef.current) return;
    const video = videoRef.current;

    // Ignore updates if I am the sender (optimistic UI)
    if (data.sender_id === user?.id) return;

    const remoteTime = data.timestamp;
    const remoteState = data.state; // 'playing' | 'paused'

    // Sync State
    if (remoteState === 'paused' && !video.paused) {
      video.pause();
    } else if (remoteState === 'playing' && video.paused) {
      video.play();
    }

    // Sync Time (Drift Correction)
    const drift = Math.abs(video.currentTime - remoteTime);
    if (drift > DRIFT_THRESHOLD) {
      console.log(`Correcting drift: ${drift}s`);
      video.currentTime = remoteTime;
    }
  }, [user, videoRef]);

  const handleMessage = useCallback((data: WebSocketMessage) => {
    switch (data.type) {
      case 'video_sync':
        handleVideoSync(data);
        break;
      case 'chat_message':
        setChatMessages(prev => [...prev, data]);
        break;
      case 'participants_update':
        setParticipants(data.participants);
        break;
      case 'emote_rain':
        triggerEmoteRain(data.emote);
        break;
      default:
        break;
    }
  }, [handleVideoSync, triggerEmoteRain]);

  useEffect(() => {
    if (!roomUuid) return;

    // Connect to WebSocket
    // Assuming backend is at localhost:8000 for dev, user should configure env.
    const wsUrl = `ws://localhost:8000/ws/watch-party/${roomUuid}/`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('Connected to WatchParty WS');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleMessage(data);
    };

    ws.onclose = () => {
      console.log('Disconnected from WatchParty WS');
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [roomUuid, handleMessage]);

  const sendSync = (state: 'playing' | 'paused', timestamp: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'sync',
        state,
        timestamp
      }));
    }
  };

  const sendMessage = (message: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'chat',
        message
      }));
    }
  };

  const sendEmote = (emote: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'emote',
        emote
      }));
    }
  };

  return {
    isConnected,
    participants,
    chatMessages,
    sendSync,
    sendMessage,
    sendEmote,
  };
}
