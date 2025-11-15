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

  const handleUpdate = async (values) => {
    try {
      const variants = JSON.parse(values.variants);
      const testData = {
        ...values,
        variants,
        start_date: values.dateRange?.[0]?.toISOString(),
        end_date: values.dateRange?.[1]?.toISOString(),
      };
      
      await api.abTesting.update(editingTest.id, testData);
      message.success('A/B тест обновлен успешно');
      setModalVisible(false);
      setEditingTest(null);
      form.resetFields();
      fetchTests();
    } catch (error) {
      message.error('Ошибка обновления A/B теста');
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.abTesting.delete(id);
      message.success('A/B тест удален успешно');
      fetchTests();
    } catch (error) {
      message.error('Ошибка удаления A/B теста');
    }
  };

  const handleActivate = async (id) => {
    try {
      await api.abTesting.activate(id);
      message.success('A/B тест активирован');
      fetchTests();
    } catch (error) {
      message.error('Ошибка активации A/B теста');
    }
  };

  const handleDeactivate = async (id) => {
    try {
      await api.abTesting.deactivate(id);
      message.success('A/B тест деактивирован');
      fetchTests();
    } catch (error) {
      message.error('Ошибка деактивации A/B теста');
    }
  };

  const openCreateModal = () => {
    setEditingTest(null);
    form.resetFields();
    form.setFieldsValue({
      traffic_allocation: 0.5,
      variants: JSON.stringify({
        variant_a: { components: [] },
        variant_b: { components: [] }
      }, null, 2)
    });
    setModalVisible(true);
  };

  const openEditModal = (test) => {
    setEditingTest(test);
    const dateRange = test.start_date && test.end_date ? 
      [dayjs(test.start_date), dayjs(test.end_date)] : null;
    
    form.setFieldsValue({
      ...test,
      variants: JSON.stringify(test.variants, null, 2),
      dateRange
    });
    setModalVisible(true);
  };

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Экран',
      dataIndex: 'screen_id',
      key: 'screen_id',
      render: (screenId) => {
        const screen = screens.find(s => s.id === screenId);
        return screen ? screen.title : `Screen #${screenId}`;
      },
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? 'Активен' : 'Неактивен'}
        </Tag>
      ),
    },
    