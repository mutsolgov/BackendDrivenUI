import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Select, DatePicker, Table, Statistic, Spin, Alert } from 'antd';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useApi } from '../../contexts/ApiContext';
import dayjs from 'dayjs';

const { Option } = Select;
const { RangePicker } = DatePicker;

const Analytics = () => {
  const [screens, setScreens] = useState([]);
  const [selectedScreen, setSelectedScreen] = useState(null);
  const [screenStats, setScreenStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState([dayjs().subtract(7, 'days'), dayjs()]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });
  const api = useApi();

  useEffect(() => {
    fetchScreens();
  }, []); 

  useEffect(() => {
    if (selectedScreen) {
      fetchScreenStats();
      setEvents([]);
      setPagination({
        current: 1,
        pageSize: 20,
        total: 0
      });

      fetchEvents(1, 20, true);
    }
  }, [selectedScreen, dateRange]); 

  const fetchScreens = async () => {
    try {
      const response = await api.screens.getAll();
      setScreens(response.data);
      if (response.data.length > 0) {
        setSelectedScreen(response.data[0].id);
      }
    } catch (error) {
      setError('Ошибка загрузки экранов');
    }
  };

  const fetchScreenStats = async () => {
    if (!selectedScreen) return;
    
    try {
      setLoading(true);
      const days = dateRange[1].diff(dateRange[0], 'days');
      const response = await api.analytics.getStats(selectedScreen, days);
      setScreenStats(response.data);
    } catch (error) {
      setError('Ошибка загрузки статистики');
    } finally {
      setLoading(false);
    }
  };

  const fetchEvents = async (page = 1, pageSize = 20, fetchCount = false) => {
    if (!selectedScreen) return;
    
    try {
      setEventsLoading(true);
      console.log('Fetching events:', { page, pageSize, screen_id: selectedScreen, fetchCount });
      
      const requests = [
        api.analytics.getEvents({
          screen_id: selectedScreen,
          limit: pageSize,
          offset: (page - 1) * pageSize
        })
      ];
      
      if (fetchCount) {
        requests.push(api.analytics.getEventsCount({
          screen_id: selectedScreen
        }));
      }
      
      const responses = await Promise.all(requests);
      const eventsResponse = responses[0];
      const countResponse = responses[1];
      
      console.log('Events response:', eventsResponse.data);
      console.log('Events response length:', eventsResponse.data?.length);
      if (countResponse) {
        console.log('Count response:', countResponse.data);
      }
      
      if (eventsResponse.data && Array.isArray(eventsResponse.data)) {
        setEvents(eventsResponse.data);
        setError(null); 
        console.log(`Loaded ${eventsResponse.data.length} events for page ${page}, pageSize ${pageSize}`);
      } else {
        console.error('Invalid events response:', eventsResponse.data);
        setEvents([]);
      }
      
      if (countResponse) {
        setPagination(prev => ({
          ...prev,
          total: countResponse.data.total
        }));
      }
      
      console.log('Updated pagination:', { current: page, pageSize, total: countResponse ? countResponse.data.total : 'unchanged' });
    } catch (error) {
      console.error('Error fetching events:', error);
      setError('Ошибка загрузки событий');
    } finally {
      setEventsLoading(false);
    }
  };

  const handleTableChange = (page, pageSize) => {
    console.log('Table change - page:', page, 'pageSize:', pageSize);
    console.log('Current pagination:', pagination);
    
    const fetchCount = pageSize !== pagination.pageSize;
    console.log('Fetch count:', fetchCount, 'pageSize changed from', pagination.pageSize, 'to', pageSize);
    
    setPagination(prev => ({
      ...prev,
      current: page,
      pageSize: pageSize
    }));
    
    fetchEvents(page, pageSize, fetchCount);
  };

  const handleShowSizeChange = (current, size) => {
    console.log('Show size change - current:', current, 'size:', size);
    
    setPagination(prev => ({
      ...prev,
      current: 1,
      pageSize: size
    }));
    
    fetchEvents(1, size, true);
  };

  const eventColumns = [
    {
      title: 'Время',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => dayjs(timestamp).format('DD.MM.YYYY HH:mm:ss'),
      width: 150,
    },
    {
      title: 'Тип события',
      dataIndex: 'event_type',
      key: 'event_type',
    },
    {
      title: 'Компонент',
      dataIndex: 'component_id',
      key: 'component_id',
      render: (componentId) => componentId || '-',
    },
    {
      title: 'Платформа',
      dataIndex: 'platform',
      key: 'platform',
    },
    {
      title: 'Пользователь',
      dataIndex: 'user_id',
      key: 'user_id',
      render: (userId) => userId ? userId.substring(0, 8) + '...' : '-',
    },
  ];


  if (error) {
    return <Alert message={error} type="error" />;
  }

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', gap: 16, alignItems: 'center' }}>
        <h2>Аналитика</h2>
        <Select
          style={{ width: 200 }}
          placeholder="Выберите экран"
          value={selectedScreen}
          onChange={setSelectedScreen}
        >
          {screens.map(screen => (
            <Option key={screen.id} value={screen.id}>
              {screen.title}
            </Option>
          ))}
        </Select>
        <RangePicker
          value={dateRange}
          onChange={setDateRange}
          format="DD.MM.YYYY"
        />
      </div>

      {loading ? (
        <Spin size="large" style={{ display: 'block', textAlign: 'center', marginTop: 100 }} />
      ) : screenStats ? (
        <>
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Просмотры"
                  value={screenStats.total_views}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Уникальные пользователи"
                  value={screenStats.unique_users}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Средняя длительность сессии"
                  value={Math.round(screenStats.avg_session_duration)}
                  suffix="сек"
                  valueStyle={{ color: '#722ed1' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Активных компонентов"
                  value={screenStats.active_components_count || screenStats.most_used_components.length}
                  valueStyle={{ color: '#eb2f96' }}
                />
              </Card>
            </Col>
          </Row>

          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col span={24}>
              <Card title="Популярные компоненты">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={screenStats.most_used_components.slice(0, 10)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="component_id" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#1890ff" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          <Card title={`События (${events.length} из ${pagination.total})`}>
            <div style={{ marginBottom: 16, fontSize: '12px', color: '#666' }}>
              Debug: current={pagination.current}, pageSize={pagination.pageSize}, total={pagination.total}, selectedScreen={selectedScreen}
            </div>
            <Table
              columns={eventColumns}
              dataSource={events}
              rowKey={(record, index) => record.id || index}
              loading={eventsLoading}
              pagination={{
                current: pagination.current,
                pageSize: pagination.pageSize,
                total: pagination.total,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} из ${total} событий`,
                pageSizeOptions: ['10', '20', '50', '100'],
                onChange: handleTableChange,
                onShowSizeChange: handleShowSizeChange,
              }}
              size="small"
            />
          </Card>
        </>
      ) : (
        <div style={{ textAlign: 'center', marginTop: 100, color: '#999' }}>
          Выберите экран для просмотра аналитики
        </div>
      )}
    </div>
  );
};

export default Analytics;





