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

  const fetchComponents = async () => {
    try {
      const response = await api.components.getAll();
      setComponents(response.data);
    } catch (error) {
      message.error('Ошибка загрузки компонентов');
    }
  };

  const handleSave = async () => {
    if (!screen.name || !screen.title) {
      message.error('Заполните обязательные поля');
      return;
    }

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }

    try {
      setSaving(true);
      setIsUpdating(true);
      setPerformanceMetrics(null);
      
      const saveTimestamp = Date.now();
      
      if (id) {
        const screenWithMetadata = {
          ...screen,
          metadata: { saveTimestamp }
        };
        
        await api.screens.update(id, screenWithMetadata);
        
        timeoutRef.current = setTimeout(() => {
          setIsUpdating(false);
          timeoutRef.current = null;
        }, 3000);
      } else {
        const response = await api.screens.create(screen);
        navigate(`/screens/builder/${response.data.id}`);
        message.success('Экран создан успешно');
        setIsUpdating(false);
      }
    } catch (error) {
      message.error('Ошибка сохранения экрана');
      setIsUpdating(false);
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    } finally {
      setSaving(false);
    }
  };
  
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handlePreview = () => {
    const previewUrl = `http://localhost:3000/preview/${screen.name}?platform=${screen.platform}&locale=${screen.locale}`;
    window.open(previewUrl, '_blank');
  };

  const handleComponentAdd = (component, targetContainerId = null) => {
    const newComponent = {
      id: uuidv4(),
      type: component.name,
      props: { ...component.config.defaultProps },
      children: []
    };

    const newConfig = { ...screen.config };
    
    const isContainerType = selectedComponent?.type === 'Container' || selectedComponent?.type === 'Card';
    
    if (targetContainerId && selectedComponent?.id === targetContainerId && isContainerType) {
      const addToContainer = (components) => {
        return components.map(comp => {
          if (comp.id === targetContainerId) {
            return {
              ...comp,
              children: [...(comp.children || []), newComponent]
            };
          }
          if (comp.children) {
            return {
              ...comp,
              children: addToContainer(comp.children)
            };
          }
          return comp;
        });
      };
      
      newConfig.components = addToContainer(newConfig.components || []);
    } else {
      newConfig.components = [...(newConfig.components || []), newComponent];
    }
    
    setScreen({ ...screen, config: newConfig });
  };

