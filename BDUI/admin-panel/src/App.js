import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import ruRU from 'antd/locale/ru_RU';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import ScreenBuilder from './pages/ScreenBuilder/ScreenBuilder';
import ScreenList from './pages/ScreenList/ScreenList';
import ComponentLibrary from './pages/ComponentLibrary/ComponentLibrary';
import Analytics from './pages/Analytics/Analytics';
import ABTesting from './pages/ABTesting/ABTesting';
import Templates from './pages/Templates/Templates';
import { ApiProvider } from './contexts/ApiContext';

function App() {
  return (
    <ConfigProvider locale={ruRU}>
      <ApiProvider>
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/screens" element={<ScreenList />} />
              <Route path="/screens/builder/:id?" element={<ScreenBuilder />} />
              <Route path="/components" element={<ComponentLibrary />} />
              <Route path="/analytics" element={<Analytics />} />
              <Route path="/ab-testing" element={<ABTesting />} />
              <Route path="/templates" element={<Templates />} />
            </Routes>
          </Layout>
        </Router>
      </ApiProvider>
    </ConfigProvider>
  );
}

export default App;





