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

  const openCreateModal = () => {
    setEditingTemplate(null);
    form.resetFields();
    form.setFieldsValue({
      config: JSON.stringify({
        type: "Container",
        props: {},
        children: []
      }, null, 2),
      is_public: true
    });
    setModalVisible(true);
  };

  const openEditModal = (template) => {
    setEditingTemplate(template);
    form.setFieldsValue({
      ...template,
      config: JSON.stringify(template.config, null, 2)
    });
    setModalVisible(true);
  };

  const extractTemplateVariables = (config) => {
    const configStr = JSON.stringify(config);
    const variables = [];
    const regex = /\{\{(\w+)\}\}/g;
    let match;
    while ((match = regex.exec(configStr)) !== null) {
      if (!variables.includes(match[1])) {
        variables.push(match[1]);
      }
    }
    return variables;
  };

  const openCreateScreenModal = (template) => {
    setSelectedTemplate(template);
    const variables = extractTemplateVariables(template.config);
    const initialVariables = {};
    variables.forEach(variable => {
      initialVariables[variable] = '';
    });
    setTemplateVariables(initialVariables);
    screenForm.resetFields();
    screenForm.setFieldsValue({
      screenName: `${template.name}_screen`,
      screenTitle: `Экран на основе ${template.name}`,
      platform: 'web',
      locale: 'ru',
      ...initialVariables
    });
    setCreateScreenModalVisible(true);
  };

  const handleCreateScreen = async (values) => {
    try {
      const { screenName, screenTitle, platform, locale, ...variables } = values;
      
      const response = await api.screens.createFromTemplate(
        selectedTemplate.id,
        screenName,
        {
          screenTitle,
          platform,
          locale,
          templateVariables: variables
        }
      );

      message.success('Экран создан успешно');
      setCreateScreenModalVisible(false);
      screenForm.resetFields();
      
      navigate(`/screen-builder/${response.data.id}`);
    } catch (error) {
      message.error('Ошибка создания экрана: ' + (error.response?.data?.detail || error.message));
    }
  };

  const groupedTemplates = templates.reduce((groups, template) => {
    const category = template.category || 'other';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(template);
    return groups;
  }, {});

  const categoryNames = {
    ecommerce: 'Электронная коммерция',
    marketing: 'Маркетинг',
    layout: 'Макеты',
    forms: 'Формы',
    other: 'Другие'
  };

