import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Dashboard from '../Dashboard';

// Mock recharts to avoid canvas errors in tests
jest.mock('recharts', () => ({
  LineChart: () => <div data-testid="line-chart" />,
  Line: () => null,
  XAxis: () => null,
  YAxis: () => null,
  CartesianGrid: () => null,
  Tooltip: () => null,
  ResponsiveContainer: ({ children }) => <div>{children}</div>,
  BarChart: () => <div data-testid="bar-chart" />,
  Bar: () => null,
}));

const mockApiContext = {
  analytics: {
    getOverview: jest.fn(),
  },
};

jest.mock('../../../contexts/ApiContext', () => ({
  useApi: () => mockApiContext,
}));

describe('Dashboard Component', () => {
  beforeEach(() => {
    mockApiContext.analytics.getOverview.mockResolvedValue({
      data: {
        total_events: 1000,
        unique_screens: 5,
        unique_users: 250,
        top_screens: [
          { name: 'home', title: 'Home', views: 500 },
          { name: 'listing', title: 'Listing', views: 300 },
        ],
        daily_stats: [
          { date: '2024-01-01', events: 100, unique_users: 20 },
          { date: '2024-01-02', events: 150, unique_users: 30 },
        ],
      },
    });
  });

  test('renders dashboard title', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Дашборд/i)).toBeInTheDocument();
    });
  });

  test('displays statistics cards', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Всего событий/i)).toBeInTheDocument();
      expect(screen.getByText(/Активных экранов/i)).toBeInTheDocument();
      expect(screen.getByText(/Уникальных пользователей/i)).toBeInTheDocument();
    });
  });

  test('displays correct statistics values', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      // Ant Design форматирует числа с запятыми
      expect(screen.getByText('1,000')).toBeInTheDocument(); // total_events (форматированное)
      expect(screen.getByText('5')).toBeInTheDocument(); // unique_screens
      expect(screen.getByText('250')).toBeInTheDocument(); // unique_users
    });
  });

  test('renders charts', async () => {
    render(
      <BrowserRouter>
        <Dashboard />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId('line-chart')).toBeInTheDocument();
    });
  });

