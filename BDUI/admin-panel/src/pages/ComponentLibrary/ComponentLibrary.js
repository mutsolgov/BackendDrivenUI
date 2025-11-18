import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Button, Modal, Form, Input, Select, message, Popconfirm, Tag } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { useApi } from '../../contexts/ApiContext';
import Editor from '@monaco-editor/react';

const { Option } = Select;

const ComponentLibrary = () => {
  const [components, setComponents] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true); 
  const [modalVisible, setModalVisible] = useState(false);
  const [editingComponent, setEditingComponent] = useState(null);
  const [form] = Form.useForm();
  const api = useApi();

  useEffect(() => {
    fetchComponents();
    fetchCategories();
  }, []); 

  const fetchComponents = async () => {
    try {
      setLoading(true);
      const response = await api.components.getAll();
      setComponents(response.data);
    } catch (error) {
      message.error('Ошибка загрузки компонентов');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.components.getCategories();
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const handleCreate = async (values) => {
    try {
      const config = JSON.parse(values.config);
      const propsSchema = values.props_schema ? JSON.parse(values.props_schema) : {};
      
      await api.components.create({
        ...values,
        config,
        props_schema: propsSchema
      });
      
      message.success('Компонент создан успешно');
      setModalVisible(false);
      form.resetFields();
      fetchComponents();
      fetchCategories();
    } catch (error) {
      message.error('Ошибка создания компонента');
    }
  };

  const handleUpdate = async (values) => {
    try {
      const config = JSON.parse(values.config);
      const propsSchema = values.props_schema ? JSON.parse(values.props_schema) : {};
      
      await api.components.update(editingComponent.id, {
        ...values,
        config,
        props_schema: propsSchema
      });
      
      message.success('Компонент обновлен успешно');
      setModalVisible(false);
      setEditingComponent(null);
      form.resetFields();
      fetchComponents();
      fetchCategories();
    } catch (error) {
      message.error('Ошибка обновления компонента');
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.components.delete(id);
      message.success('Компонент удален успешно');
      fetchComponents();
    } catch (error) {
      message.error('Ошибка удаления компонента');
    }
  };

 
