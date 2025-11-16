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
      
