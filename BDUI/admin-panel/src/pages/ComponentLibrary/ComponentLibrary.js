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

  const openCreateModal = () => {
    setEditingComponent(null);
    form.resetFields();
    form.setFieldsValue({
      config: JSON.stringify({
        defaultProps: {}
      }, null, 2),
      props_schema: JSON.stringify({}, null, 2)
    });
    setModalVisible(true);
  };

  const openEditModal = (component) => {
    setEditingComponent(component);
    form.setFieldsValue({
      ...component,
      config: JSON.stringify(component.config, null, 2),
      props_schema: JSON.stringify(component.props_schema || {}, null, 2)
    });
    setModalVisible(true);
  };

  const groupedComponents = components.reduce((groups, component) => {
    const category = component.category || 'other';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push(component);
    return groups;
  }, {});

  const categoryNames = {
    basic: 'Основные',
    layout: 'Макет',
    form: 'Формы',
    data: 'Данные',
    media: 'Медиа',
    marketing: 'Маркетинг',
    other: 'Другие'
  };

  return (
    <div>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2>Библиотека компонентов</h2>
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreateModal}>
          Создать компонент
        </Button>
      </div>

      {Object.entries(groupedComponents).map(([category, categoryComponents]) => (
        <div key={category} style={{ marginBottom: 32 }}>
          <h3 style={{ marginBottom: 16, borderBottom: '1px solid #d9d9d9', paddingBottom: 8 }}>
            {categoryNames[category] || category}
          </h3>
          <Row gutter={[16, 16]}>
            {categoryComponents.map(component => (
              <Col key={component.id} xs={24} sm={12} md={8} lg={6}>
                <Card
                  size="small"
                  title={
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span>{component.name}</span>
                      {component.is_system && <Tag color="blue">Системный</Tag>}
                    </div>
                  }
                  extra={
                    !component.is_system && (
                      <div>
                        <Button
                          type="text"
                          size="small"
                          icon={<EditOutlined />}
                          onClick={() => openEditModal(component)}
                        />
                        <Popconfirm
                          title="Удалить компонент?"
                          onConfirm={() => handleDelete(component.id)}
                          okText="Да"
                          cancelText="Нет"
                        >
                          <Button
                            type="text"
                            size="small"
                            danger
                            icon={<DeleteOutlined />}
                          />
                        </Popconfirm>
                      </div>
                    )
                  }
                >
                  <div style={{ marginBottom: 8 }}>
                    <Tag color="green">{component.type}</Tag>
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {Object.keys(component.props_schema || {}).length} свойств
                  </div>
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      ))}

      <Modal
        title={editingComponent ? 'Редактировать компонент' : 'Создать компонент'}
        open={modalVisible}
        onOk={() => form.submit()}
        onCancel={() => {
          setModalVisible(false);
          setEditingComponent(null);
          form.resetFields();
        }}
        okText={editingComponent ? 'Обновить' : 'Создать'}
        cancelText="Отмена"
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={editingComponent ? handleUpdate : handleCreate}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="Название"
                rules={[{ required: true, message: 'Введите название компонента' }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="type"
                label="Тип"
                rules={[{ required: true, message: 'Введите тип компонента' }]}
              >
                <Input />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="category"
            label="Категория"
            rules={[{ required: true, message: 'Выберите категорию' }]}
          >
            <Select allowClear showSearch>
              {categories.map(cat => (
                <Option key={cat} value={cat}>{categoryNames[cat] || cat}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="config"
            label="Конфигурация (JSON)"
            rules={[{ required: true, message: 'Введите конфигурацию компонента' }]}
          >
            <Editor
              height="200px"
              language="json"
              theme="vs-dark"
              options={{
                minimap: { enabled: false },
                scrollBeyondLastLine: false,
              }}
            />
          </Form.Item>

          <Form.Item
            name="props_schema"
            label="Схема свойств (JSON)"
          >
            <Editor
              height="200px"
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
    </div>
  );
};

export default ComponentLibrary;





