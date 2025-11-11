import React, { useState } from 'react';
import { Layout as AntLayout, Menu, theme } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  AppstoreOutlined,
  BuildOutlined,
  BarChartOutlined,
  ExperimentOutlined,
  FileTextOutlined,
  DesktopOutlined,
} from '@ant-design/icons';

const { Header, Sider, Content } = AntLayout;

const Layout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { colorBgContainer },
  } = theme.useToken();

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: 'Дашборд',
    },
    {
      key: '/screens',
      icon: <DesktopOutlined />,
      label: 'Экраны',
    },
    {
      key: '/screens/builder',
      icon: <BuildOutlined />,
      label: 'Конструктор',
    },
    {
      key: '/components',
      icon: <AppstoreOutlined />,
      label: 'Компоненты',
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: 'Аналитика',
    },
    {
      key: '/ab-testing',
      icon: <ExperimentOutlined />,
      label: 'A/B тесты',
    },
    {
      key: '/templates',
      icon: <FileTextOutlined />,
      label: 'Шаблоны',
    },
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  const getSelectedKey = () => {
    const path = location.pathname;
    if (path.startsWith('/screens/builder')) return '/screens/builder';
    return path;
  };

  return (
    <div className="app-container">
      <AntLayout style={{ minHeight: '100vh' }}>
        <Sider trigger={null} collapsible collapsed={collapsed}>
          <div style={{
            height: 32,
            margin: 16,
            background: 'rgba(255, 255, 255, 0.2)',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold',
          }}>
            {collapsed ? 'BDUI' : 'BDUI Admin'}
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[getSelectedKey()]}
            items={menuItems}
            onClick={handleMenuClick}
          />
        </Sider>
        <AntLayout>
          <Header
            style={{
              padding: 0,
              background: colorBgContainer,
              display: 'flex',
              alignItems: 'center',
              paddingLeft: 16,
            }}
          >
            <button
              type="button"
              onClick={() => setCollapsed(!collapsed)}
              style={{
                fontSize: '16px',
                width: 64,
                height: 64,
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
              }}
            >
              {collapsed ? '☰' : '✕'}
            </button>
            <h1 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
              Backend Driven UI Framework
            </h1>
          </Header>
          <Content
            style={{
              margin: '24px 16px',
              padding: 24,
              minHeight: 280,
              background: colorBgContainer,
              borderRadius: 8,
            }}
          >
            <div className="content-container">
              {children}
            </div>
          </Content>
        </AntLayout>
      </AntLayout>
    </div>
  );
};

export default Layout;





