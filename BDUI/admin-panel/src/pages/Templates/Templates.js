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

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Шаблоны</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          Создать шаблон
        </Button>
      </div>

      {Object.entries(groupedTemplates).map(([category, categoryTemplates]) => (
        <div key={category} style={{ marginBottom: 32 }}>
          <h3 style={{ marginBottom: 16, borderBottom: '1px solid #d9d9d9', paddingBottom: 8 }}>
            {categoryNames[category] || category}
          </h3>
          <Row gutter={[16, 16]}>
            {categoryTemplates.map(template => (
              <Col key={template.id} xs={24} sm={12} md={8} lg={6}>
                <Card
                  className="template-card"
                  size="small"
                  title={
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <FileTextOutlined />
                      <span>{template.name}</span>
                    </div>
                  }
                  extra={
                    <div style={{ display: 'flex', gap: 4 }}>
                      {template.is_public && <Tag color="green">Публичный</Tag>}
                      {template.parent_id && <Tag color="orange">Унаследован</Tag>}
                    </div>
                  }
                  actions={[
                    <Button
                      key="edit"
                      type="text"
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => openEditModal(template)}
                      title="Редактировать"
                    />,
                    <Button
                      key="inherit"
                      type="text"
                      size="small"
                      icon={<CopyOutlined />}
                      onClick={() => handleInherit(template)}
                      title="Наследовать"
                    />,
                    <Button
                      key="create-screen"
                      type="text"
                      size="small"
                      icon={<FileAddOutlined />}
                      onClick={() => openCreateScreenModal(template)}
                      title="Создать экран на основе шаблона"
                      style={{ color: '#1890ff' }}
                    />,
                    <Popconfirm
                      key="delete"
                      title="Удалить шаблон?"
                      onConfirm={() => handleDelete(template.id)}
                      okText="Да"
                      cancelText="Нет"
                    >
                      <Button
                        type="text"
                        size="small"
                        danger
                        icon={<DeleteOutlined />}
                        title="Удалить"
                      />
                    </Popconfirm>
                  ]}
                >
                  <div style={{ marginBottom: 8, fontSize: '12px', color: '#666' }}>
                    {template.description || 'Без описания'}
                  </div>
                  <div style={{ fontSize: '11px', color: '#999' }}>
                    Создан: {new Date(template.created_at).toLocaleDateString()}
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      ))}

      <Modal
        title={editingTemplate ? 'Редактировать шаблон' : 'Создать шаблон'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false);
          setEditingTemplate(null);
          form.resetFields();
        }}
        okText={editingTemplate ? 'Обновить' : 'Создать'}
        cancelText="Отмена"
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={editingTemplate ? handleUpdate : handleCreate}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="Название"
                rules={[{ required: true, message: 'Введите название шаблона' }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="category"
                label="Категория"
                rules={[{ required: true, message: 'Выберите категорию' }]}
              >
                <Select allowClear showSearch>
                  {categories.map(cat => (
                    <Option key={cat} value={cat}>{categoryNames[cat] || cat}</Option>
                  ))}
                  <Option value="ecommerce">Электронная коммерция</Option>
                  <Option value="marketing">Маркетинг</Option>
                  <Option value="layout">Макеты</Option>
                  <Option value="forms">Формы</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="Описание"
          >
            <TextArea placeholder="Описание шаблона" rows={3} />
          </Form.Item>

          <Form.Item
            name="is_public"
            label="Публичный шаблон"
            valuePropName="checked"
          >
            <input type="checkbox" />
          </Form.Item>

          <Form.Item
            name="config"
            label="Конфигурация (JSON)"
            rules={[{ required: true, message: 'Введите конфигурацию шаблона' }]}
          >
            <Editor
              height="400px"
              language="json"
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
              }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Модальное окно для создания экрана из шаблона */}
      <Modal
        title={`Создать экран на основе шаблона "${selectedTemplate?.name}"`}
        open={createScreenModalVisible}
        onOk={() => screenForm.submit()}
        onCancel={() => {
          setCreateScreenModalVisible(false);
          setSelectedTemplate(null);
          setTemplateVariables({});
          screenForm.resetFields();
        }}
        okText="Создать экран"
        cancelText="Отмена"
        width={600}
      >
        <Form
          form={screenForm}
          layout="vertical"
          onFinish={handleCreateScreen}
        >
          <Form.Item
            name="screenName"
            label="Название экрана"
            rules={[{ required: true, message: 'Введите название экрана' }]}
          >
            <Input placeholder="Введите название экрана" />
          </Form.Item>

          <Form.Item
            name="screenTitle"
            label="Заголовок экрана"
            rules={[{ required: true, message: 'Введите заголовок экрана' }]}
          >
            <Input placeholder="Введите заголовок экрана" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="platform"
                label="Платформа"
                rules={[{ required: true, message: 'Выберите платформу' }]}
              >
                <Select>
                  <Option value="web">Web</Option>
                  <Option value="mobile">Mobile</Option>
                  <Option value="tablet">Tablet</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="locale"
                label="Язык"
                rules={[{ required: true, message: 'Выберите язык' }]}
              >
                <Select>
                  <Option value="ru">Русский</Option>
                  <Option value="en">English</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          {selectedTemplate && extractTemplateVariables(selectedTemplate.config).length > 0 && (
            <>
              <div style={{ marginBottom: 16, fontWeight: 'bold' }}>
                Переменные шаблона:
              </div>
              {extractTemplateVariables(selectedTemplate.config).map(variable => (
                <Form.Item
                  key={variable}
                  name={variable}
                  label={`${variable}`}
                  rules={[{ required: true, message: `Введите значение для ${variable}` }]}
                >
                  <Input placeholder={`Введите значение для ${variable}`} />
                </Form.Item>
              ))}
            </>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default Templates;





