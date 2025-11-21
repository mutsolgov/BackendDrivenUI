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


