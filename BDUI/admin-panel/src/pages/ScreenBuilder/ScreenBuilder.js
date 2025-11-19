import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button, message, Spin, Input, Select, Switch } from 'antd';
import { SaveOutlined, EyeOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import ComponentPalette from './components/ComponentPalette';
import Canvas from './components/Canvas';
import PropertiesPanel from './components/PropertiesPanel';
import PerformanceMonitor from '../../components/PerformanceMonitor/PerformanceMonitor';
import { useApi } from '../../contexts/ApiContext';
import { useAdminWebSocket } from '../../hooks/useAdminWebSocket';
import { v4 as uuidv4 } from 'uuid';

const { Option } = Select;

const ScreenBuilder = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const api = useApi();
  
  const [screen, setScreen] = useState(null);
  const [components, setComponents] = useState([]);
  const [selectedComponent, setSelectedComponent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  
  const timeoutRef = useRef(null);
  
  const handleWebSocketMessage = useCallback((data) => {
    console.log('📨 ScreenBuilder: WebSocket message', data);
    
    if (data.type === 'screen_update' && data.performance) {
      const perf = data.performance;
      const receivedAt = Date.now();
      
      const websocketTime = receivedAt - perf.websocket_sent_at;
      
      const fullMetrics = {
        total: receivedAt - perf.save_timestamp,
        db_time: perf.db_time,
        backend_time: perf.backend_time,
        websocket_time: websocketTime,
        client_time: 0 
      };
      
      console.log('⚡ ScreenBuilder: Setting performance metrics', fullMetrics);
      
      setPerformanceMetrics(fullMetrics);
      
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      
      setTimeout(() => {
        setIsUpdating(false);
        message.success({
          content: `Экран обновлен за ${fullMetrics.total.toFixed(0)}ms`,
          key: 'screen-update', 
          duration: 2
        });
      }, 500);
    }
  }, []);
  
  const { isConnected } = useAdminWebSocket(handleWebSocketMessage);

  useEffect(() => {
    const initializeData = async () => {
      try {
        if (id) {
          await fetchScreen();
        } else {
          setScreen({
            name: '',
            title: '',
            description: '',
            platform: 'web',
            locale: 'ru',
            is_active: true,
            config: { components: [] }
          });
        }
        await fetchComponents();
      } catch (error) {
        console.error('Error initializing data:', error);
      } finally {
        setLoading(false);
      }
    };

    initializeData();
  }, [id]); 

  const fetchScreen = async () => {
    try {
      const response = await api.screens.getById(id);
      setScreen(response.data);
    } catch (error) {
      message.error('Ошибка загрузки экрана');
      navigate('/screens');
    } finally {
      setLoading(false);
    }
  };

