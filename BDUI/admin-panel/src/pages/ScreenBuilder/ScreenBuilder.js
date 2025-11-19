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

  const updateComponent = (componentId, updates) => {
    console.log('updateComponent called:', componentId, updates);
    
    const updateComponentRecursive = (components) => {
      return components.map(comp => {
        if (comp.id === componentId) {
          console.log('Updating component:', comp, 'with:', updates);
          return { ...comp, ...updates };
        }
        if (comp.children) {
          return { ...comp, children: updateComponentRecursive(comp.children) };
        }
        return comp;
      });
    };

    const newConfig = { ...screen.config };
    newConfig.components = updateComponentRecursive(newConfig.components || []);
    setScreen({ ...screen, config: newConfig });
    

    if (selectedComponent?.id === componentId) {
      console.log('Updating selectedComponent:', selectedComponent, 'with:', updates);
      setSelectedComponent({ ...selectedComponent, ...updates });
    }
    
  };


  const deleteComponent = (componentId) => {
    const deleteComponentRecursive = (components) => {
      return components.filter(comp => {
        if (comp.id === componentId) {
          return false;
        }
        if (comp.children) {
          comp.children = deleteComponentRecursive(comp.children);
        }
        return true;
      });
    };

    const newConfig = { ...screen.config };
    newConfig.components = deleteComponentRecursive(newConfig.components || []);
    setScreen({ ...screen, config: newConfig });
    
    if (selectedComponent?.id === componentId) {
      setSelectedComponent(null);
    }
  };

  const moveComponentUp = (componentId) => {
    const moveUpRecursive = (components) => {
      for (let i = 0; i < components.length; i++) {
        if (components[i].id === componentId) {
          if (i > 0) {
            const newComponents = [...components];
            [newComponents[i - 1], newComponents[i]] = [newComponents[i], newComponents[i - 1]];
            return { found: true, newComponents };
          }
          return { found: true, newComponents: components }; 
        }
        
        if (components[i].children) {
          const result = moveUpRecursive(components[i].children);
          if (result.found) {
            const newComponents = [...components];
            newComponents[i] = {
              ...newComponents[i],
              children: result.newComponents
            };
            return { found: true, newComponents };
          }
        }
      }
      return { found: false, newComponents: components };
    };

    const result = moveUpRecursive(screen.config.components || []);
    if (result.found) {
      const newConfig = { ...screen.config, components: result.newComponents };
      setScreen({ ...screen, config: newConfig });
    }
  };

  const moveComponentDown = (componentId) => {
    const moveDownRecursive = (components) => {
      for (let i = 0; i < components.length; i++) {
        if (components[i].id === componentId) {
          if (i < components.length - 1) {
            const newComponents = [...components];
            [newComponents[i], newComponents[i + 1]] = [newComponents[i + 1], newComponents[i]];
            return { found: true, newComponents };
          }
          return { found: true, newComponents: components }; 
        }
        
        if (components[i].children) {
          const result = moveDownRecursive(components[i].children);
          if (result.found) {
            const newComponents = [...components];
            newComponents[i] = {
              ...newComponents[i],
              children: result.newComponents
            };
            return { found: true, newComponents };
          }
        }
      }
      return { found: false, newComponents: components };
    };

    const result = moveDownRecursive(screen.config.components || []);
    if (result.found) {
      const newConfig = { ...screen.config, components: result.newComponents };
      setScreen({ ...screen, config: newConfig });
    }
  };

  if (loading || !screen || components.length === 0) {
    return <Spin size="large" style={{ display: 'block', textAlign: 'center', marginTop: 100 }} />;
  }

  return (
    <div className="screen-builder">
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
          <Input
            placeholder="Название экрана"
            value={screen.name}
            onChange={(e) => setScreen({ ...screen, name: e.target.value })}
            style={{ width: 200 }}
          />
          <Input
            placeholder="Заголовок экрана"
            value={screen.title}
            onChange={(e) => setScreen({ ...screen, title: e.target.value })}
            style={{ width: 300 }}
          />
          <Select
            value={screen.platform}
            onChange={(value) => setScreen({ ...screen, platform: value })}
            style={{ width: 120 }}
          >
            <Option value="web">Web</Option>
            <Option value="android">Android</Option>
            <Option value="ios">iOS</Option>
          </Select>
          <Select
            value={screen.locale}
            onChange={(value) => setScreen({ ...screen, locale: value })}
            style={{ width: 100 }}
          >
            <Option value="ru">RU</Option>
            <Option value="en">EN</Option>
          </Select>
          <Switch
            checked={screen.is_active}
            onChange={(checked) => setScreen({ ...screen, is_active: checked })}
            checkedChildren="Активен"
            unCheckedChildren="Неактивен"
          />
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button
            icon={<EyeOutlined />}
            onClick={handlePreview}
            disabled={!screen.name}
          >
            Предпросмотр
          </Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={handleSave}
            loading={saving}
          >
            Сохранить
          </Button>
        </div>
      </div>

      {/* Performance Monitor */}
      <PerformanceMonitor 
        isUpdating={isUpdating}
        metrics={performanceMetrics}
        onComplete={() => {
          setIsUpdating(false);
          setPerformanceMetrics(null);
        }}
      />

      <div className="builder-content">
        <ComponentPalette 
          components={components} 
          selectedComponent={selectedComponent}
          onComponentAdd={(component) => handleComponentAdd(component, selectedComponent?.id)} 
        />
        
        <Canvas
          config={screen.config}
          selectedComponent={selectedComponent}
          onSelectComponent={setSelectedComponent}
          onUpdateComponent={updateComponent}
          onDeleteComponent={deleteComponent}
          onAddToContainer={handleComponentAdd}
          onMoveUp={moveComponentUp}
          onMoveDown={moveComponentDown}
        />
        
        <PropertiesPanel
          selectedComponent={selectedComponent}
          components={components}
          onUpdateComponent={updateComponent}
        />
      </div>
    </div>
  );
};

export default ScreenBuilder;





