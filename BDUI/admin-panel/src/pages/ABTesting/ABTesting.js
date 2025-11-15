import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, message, Popconfirm, Tag, DatePicker, InputNumber, Alert } from 'antd';
import { PlusOutlined, PlayCircleOutlined, PauseCircleOutlined, EditOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { useApi } from '../../contexts/ApiContext';
import Editor from '@monaco-editor/react';
import dayjs from 'dayjs';

const { Option } = Select;
const { TextArea } = Input;
const { RangePicker } = DatePicker;

const ABTesting = () => {
  const [tests, setTests] = useState([]);
  const [screens, setScreens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTest, setEditingTest] = useState(null);
  const [form] = Form.useForm();
  const api = useApi();

  useEffect(() => {
    fetchTests();
    fetchScreens();
  }, []); 

  const fetchTests = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching A/B tests...');
      const response = await api.abTesting.getAll();
      console.log('A/B tests response:', response);
      console.log('A/B tests data:', response.data);
      
      if (response.data && Array.isArray(response.data)) {
        setTests(response.data);
        console.log(`Loaded ${response.data.length} A/B tests`);
      } else {
        console.error('Invalid A/B tests response:', response.data);
        setTests([]);
        const errorMsg = 'Получены некорректные данные A/B тестов';
        setError(errorMsg);
        message.error(errorMsg);
      }
    } catch (error) {
      console.error('Error fetching A/B tests:', error);
      console.error('Error details:', error.response?.data);
      setTests([]);
      
      let errorMessage = 'Ошибка загрузки A/B тестов';
      if (error.response?.status === 404) {
        errorMessage = 'API endpoint для A/B тестов не найден';
      } else if (error.response?.status === 500) {
        errorMessage = 'Внутренняя ошибка сервера при загрузке A/B тестов';
      } else if (error.message) {
        errorMessage = `Ошибка: ${error.message}`;
      }
      
      setError(errorMessage);
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const fetchScreens = async () => {
    try {
      console.log('Fetching screens for A/B tests...');
      const response = await api.screens.getAll();
      console.log('Screens response:', response);
      
      if (response.data && Array.isArray(response.data)) {
        setScreens(response.data);
        console.log(`Loaded ${response.data.length} screens`);
      } else {
        console.error('Invalid screens response:', response.data);
        setScreens([]);
      }
    } catch (error) {
      console.error('Error fetching screens:', error);
      console.error('Error details:', error.response?.data);
      setScreens([]);
    }
  };

  const handleCreate = async (values) => {
    try {
      const variants = JSON.parse(values.variants);
      const testData = {
        ...values,
        variants,
        start_date: values.dateRange?.[0]?.toISOString(),
        end_date: values.dateRange?.[1]?.toISOString(),
      };
      
      await api.abTesting.create(testData);
      message.success('A/B тест создан успешно');
      setModalVisible(false);
      form.resetFields();
      fetchTests();
    } catch (error) {
      message.error('Ошибка создания A/B теста');
    }
  };
