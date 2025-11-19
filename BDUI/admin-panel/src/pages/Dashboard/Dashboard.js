import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, List, Typography, Spin, Alert } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useApi } from '../../contexts/ApiContext';

const { Title } = Typography;

const Dashboard = () => {
  const [overview, setOverview] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const api = useApi();

  useEffect(() => {
    fetchOverview();
  }, []); 

  const fetchOverview = async () => {
    try {
      setLoading(true);
      const response = await api.analytics.getOverview(7);
      setOverview(response.data);
    } catch (err) {
      setError('Ошибка загрузки данных');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <Spin size="large" style={{ display: 'block', textAlign: 'center', marginTop: 100 }} />;
  }

  if (error) {
    return <Alert message={error} type="error" />;
  }

  const dailyStatsData = overview?.daily_stats || [];
  const topScreensData = overview?.top_screens || [];

  return (
    <div>
      <Title level={2}>Дашборд</Title>
      
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Всего событий"
              value={overview?.total_events || 0}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Активных экранов"
              value={overview?.unique_screens || 0}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Уникальных пользователей"
              value={overview?.unique_users || 0}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Конверсия"
              value={overview?.unique_users ? ((overview.unique_users / overview.total_events) * 100).toFixed(1) : 0}
              suffix="%"
              valueStyle={{ color: '#eb2f96' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={16}>
          <Card title="Активность за неделю">
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={dailyStatsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="events" stroke="#1890ff" name="События" />
                <Line type="monotone" dataKey="unique_users" stroke="#52c41a" name="Пользователи" />
            
