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

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'pong') {
            return;
          }
          
          console.log('📨 Admin WebSocket: Message received', data);
          
          if (onMessageRef.current) {
            onMessageRef.current(data);
          }
        } catch (err) {
          console.error('❌ Admin WebSocket: Parse error', err);
        }
      };

      ws.onclose = (event) => {
        console.log('🔌 Admin WebSocket: Disconnected', event.code);
        setIsConnected(false);
        wsRef.current = null;
        
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`🔄 Admin WebSocket: Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`);
    
