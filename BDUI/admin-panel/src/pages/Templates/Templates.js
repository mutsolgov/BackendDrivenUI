import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Button, Modal, Form, Input, Select, message, Popconfirm, Tag, Space } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, CopyOutlined, FileTextOutlined, FileAddOutlined } from '@ant-design/icons';
import { useApi } from '../../contexts/ApiContext';
import { useNavigate } from 'react-router-dom';
import Editor from '@monaco-editor/react';

const { Option } = Select;
const { TextArea } = Input;

const Templates = () => {
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true); 
  const [modalVisible, setModalVisible] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [createScreenModalVisible, setCreateScreenModalVisible] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [templateVariables, setTemplateVariables] = useState({});
  const [form] = Form.useForm();
  const [screenForm] = Form.useForm();
  const api = useApi();
  const navigate = useNavigate();

  useEffect(() => {
    fetchTemplates();
    fetchCategories();
  }, []); 

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await api.templates.getAll();
      setTemplates(response.data);
    } catch (error) {
      message.error('Ошибка загрузки шаблонов');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await api.templates.getCategories();
      setCategories(response.data);
    } catch (error) {
      console.error('Error fetching categories:', error);
    }
  };

  const handleCreate = async (values) => {
    try {
      const config = JSON.parse(values.config);
      await api.templates.create({
        ...values,
        config
      });
      
      message.success('Шаблон создан успешно');
      setModalVisible(false);
      form.resetFields();
      fetchTemplates();
      fetchCategories();
    } catch (error) {
      message.error('Ошибка создания шаблона');
    }
  };

  const handleUpdate = async (values) => {
    try {
      const config = JSON.parse(values.config);
      await api.templates.update(editingTemplate.id, {
        ...values,
        config
      });
      
      message.success('Шаблон обновлен успешно');
      setModalVisible(false);
      setEditingTemplate(null);
      form.resetFields();
      fetchTemplates();
      fetchCategories();
    } catch (error) {
      message.error('Ошибка обновления шаблона');
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.templates.delete(id);
      message.success('Шаблон удален успешно');
      fetchTemplates();
    } catch (error) {
      message.error('Ошибка удаления шаблона');
    }
  };

  const handleInherit = async (template) => {
    try {
      const newName = `${template.name}_inherited_${Date.now()}`;
      await api.templates.inherit(template.id, newName);
      message.success('Шаблон унаследован успешно');
      fetchTemplates();
    } catch (error) {
      message.error('Ошибка наследования шаблона');
    }
  };

