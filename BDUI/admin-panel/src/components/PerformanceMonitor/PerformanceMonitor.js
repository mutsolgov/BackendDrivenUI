import React, { useState, useEffect } from 'react';
import { Card, Progress, Typography, Space } from 'antd';
import { ThunderboltOutlined, CheckCircleOutlined, LoadingOutlined } from '@ant-design/icons';
import './PerformanceMonitor.css';

const { Text, Title } = Typography;

const STAGES = [
  { key: 'broadcast', label: 'Передача', icon: '📡', color: '#722ed1' }
];

const PerformanceMonitor = ({ isUpdating, metrics, onComplete }) => {
  const [currentStage, setCurrentStage] = useState(0);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [stageTimings, setStageTimings] = useState({});
  const [startTime, setStartTime] = useState(null);
  const [isComplete, setIsComplete] = useState(false);
  const [hasRealMetrics, setHasRealMetrics] = useState(false);

  useEffect(() => {
    if (isUpdating && !startTime && !isComplete) {
      console.log('🚀 PerformanceMonitor: Start monitoring');
      setStartTime(Date.now());
      setCurrentStage(0);
      setStageTimings({});
      setElapsedTime(0);
      setIsComplete(false);
      setHasRealMetrics(false);
    }
  }, [isUpdating, startTime, isComplete]);

  useEffect(() => {
    if (!isUpdating || !startTime || isComplete) return;

    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      setElapsedTime(elapsed);

      setCurrentStage(0);

      if (!hasRealMetrics) {
        setStageTimings({
          broadcast: elapsed
        });
      }
    }, 30);

    return () => {
      console.log('🛑 PerformanceMonitor: Interval cleared');
      clearInterval(interval);
    };
  }, [isUpdating, startTime, isComplete, hasRealMetrics]);

  useEffect(() => {
    if (metrics && metrics.total && !isComplete) {
      console.log('✅ PerformanceMonitor: Received real metrics:', metrics);
      
      setHasRealMetrics(true);
      
      setIsComplete(true);
      
      const wsTime = metrics.websocket_time || 0;
      
      setStageTimings({
        broadcast: wsTime
      });
      setElapsedTime(metrics.total);
      setCurrentStage(1); 
      
      console.log('📊 Final timings:', {
        broadcast: wsTime,
        total: metrics.total
      });
      
      const timer = setTimeout(() => {
        console.log('🔄 PerformanceMonitor: Resetting after 3s');
        if (onComplete) onComplete();
        setStartTime(null);
        setCurrentStage(0);
        setIsComplete(false);
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [metrics, isComplete, onComplete]);

  if (!isUpdating && currentStage === 0 && !isComplete) {
    return null;
  }

  const totalTime = metrics?.total || elapsedTime;

  return (
    <Card 
      className="performance-monitor"
      style={{ 
        marginBottom: 16,
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        borderRadius: 8,
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        color: 'white'
      }}
    >
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* Заголовок */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            {isComplete ? (
              <CheckCircleOutlined style={{ fontSize: 24, color: '#52c41a' }} />
            ) : (
              <LoadingOutlined style={{ fontSize: 24, color: 'white' }} spin />
            )}
            <Title level={4} style={{ margin: 0, color: 'white' }}>
              {isComplete ? 'Обновление завершено!' : 'Обновление экрана...'}
            </Title>
          </Space>
          <Space align="center">
            <ThunderboltOutlined style={{ fontSize: 20, color: '#fadb14' }} />
            <Text strong style={{ fontSize: 28, color: 'white' }}>
              {totalTime.toFixed(0)}ms
            </Text>
          </Space>
        </div>


        {/* Итоговая статистика */}
        {isComplete && (
          <div style={{ 
            textAlign: 'center', 
            background: 'rgba(255,255,255,0.2)', 
            padding: 12, 
            borderRadius: 8 
          }}>
            <Text style={{ color: 'white', fontSize: 14 }}>
              {totalTime < 50 ? '⚡⚡⚡ Молниеносно!' : 
               totalTime < 100 ? '⚡⚡ Очень быстро!' : 
               totalTime < 200 ? '⚡ Быстро!' : 'Обновлено'}
            </Text>
          </div>
        )}
      </Space>
    </Card>
  );
};

export default PerformanceMonitor;

