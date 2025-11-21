import React, { useState, useEffect } from 'react';
import { Table, Button, Space, Modal, Form, Input, Select, message, Popconfirm, Tag } from 'antd';
import { EditOutlined, DeleteOutlined, CopyOutlined, PlusOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../../contexts/ApiContext';

const { Option } = Select;

const ScreenList = () => {
  const [screens, setScreens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const api = useApi();

  useEffect(() => {
    fetchScreens();
  }, []); 

  const fetchScreens = async () => {
    try {
      setLoading(true);
      const response = await api.screens.getAll();
      setScreens(response.data);
      setPagination(prev => ({
        ...prev,
        total: response.data.length
      }));
    } catch (error) {
      message.error('Ошибка загрузки экранов');
      console.error('Error fetching screens:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (values) => {
    try {
      await api.screens.create({
        ...values,
        config: { components: [] }
      });
      message.success('Экран создан успешно');
      setModalVisible(false);
      form.resetFields();
      fetchScreens();
    } catch (error) {
      message.error('Ошибка создания экрана');
      console.error('Error creating screen:', error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.screens.delete(id);
      message.success('Экран удален успешно');
      fetchScreens();
    } catch (error) {
      message.error('Ошибка удаления экрана');
      console.error('Error deleting screen:', error);
    }
  };

  const handleDuplicate = async (screen) => {
    try {
      const newName = `${screen.name}_copy_${Date.now()}`;
      await api.screens.duplicate(screen.id, newName);
      message.success('Экран скопирован успешно');
      fetchScreens();
    } catch (error) {
      message.error('Ошибка копирования экрана');
      console.error('Error duplicating screen:', error);
    }
  };

  const handleTableChange = (paginationConfig) => {
    setPagination(paginationConfig);
  };

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Button type="link" onClick={() => navigate(`/screens/builder/${record.id}`)}>
          {text}
        </Button>
      ),
    },
    {
      title: 'Заголовок',
      dataIndex: 'title',
      key: 'title',
    },
    {
      title: 'Платформа',
      dataIndex: 'platform',
      key: 'platform',
      render: (platform) => (
        <Tag color={platform === 'web' ? 'blue' : platform === 'android' ? 'green' : 'orange'}>
          {platform.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Локаль',
      dataIndex: 'locale',
      key: 'locale',
      render: (locale) => <Tag>{locale.toUpperCase()}</Tag>,
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
    {
      title: 'Версия',
      dataIndex: 'version',
      key: 'version',
      render: (version) => <Tag color="purple">v{version}</Tag>,
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_, record) => (
        <Space size="middle">
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => navigate(`/screens/builder/${record.id}`)}
            size="small"
          
