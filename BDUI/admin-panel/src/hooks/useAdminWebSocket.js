import { useEffect, useRef, useState, useCallback } from 'react';

export const useAdminWebSocket = (onMessage) => {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  
  const onMessageRef = useRef(onMessage);
  
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('⚠️ Admin WebSocket: Already connected');
      return;
    }
    
    try {
      const wsUrl = 'ws://localhost:8000/ws/admin';
      console.log('🔌 Admin WebSocket: Connecting to', wsUrl);
      
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('✅ Admin WebSocket: Connected');
        setIsConnected(true);
        reconnectAttempts.current = 0;
        
        ws.send(JSON.stringify({ type: 'ping' }));
      };


