import React from 'react';
import { Row, Col, Card, Statistic, Progress, Table, Tag } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  ShoppingCartOutlined,
  ScheduleOutlined,
  InboxOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import type { ColumnsType } from 'antd/es/table';

interface OrderData {
  key: string;
  orderNo: string;
  customer: string;
  product: string;
  quantity: number;
  deliveryDate: string;
  status: string;
  progress: number;
}

const Dashboard: React.FC = () => {
  // 模拟数据
  const recentOrders: OrderData[] = [
    {
      key: '1',
      orderNo: 'BD400-001',
      customer: '客户A',
      product: '产品X',
      quantity: 1000,
      deliveryDate: '2024-02-15',
      status: '生产中',
      progress: 65
    },
    {
      key: '2',
      orderNo: 'BD400-002',
      customer: '客户B',
      product: '产品Y',
      quantity: 500,
      deliveryDate: '2024-02-20',
      status: '待生产',
      progress: 0
    },
    {
      key: '3',
      orderNo: 'BD400-003',
      customer: '客户C',
      product: '产品Z',
      quantity: 800,
      deliveryDate: '2024-02-10',
      status: '已完成',
      progress: 100
    }
  ];

  const columns: ColumnsType<OrderData> = [
    {
      title: '订单号',
      dataIndex: 'orderNo',
      key: 'orderNo',
    },
    {
      title: '客户',
      dataIndex: 'customer',
      key: 'customer',
    },
    {
      title: '产品',
      dataIndex: 'product',
      key: 'product',
    },
    {
      title: '数量',
      dataIndex: 'quantity',
      key: 'quantity',
    },
    {
      title: '交期',
      dataIndex: 'deliveryDate',
      key: 'deliveryDate',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        let color = 'default';
        if (status === '生产中') color = 'processing';
        if (status === '已完成') color = 'success';
        if (status === '待生产') color = 'warning';
        return <Tag color={color}>{status}</Tag>;
      },
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress: number) => (
        <Progress percent={progress} size="small" />
      ),
    },
  ];

  // 生产趋势图表配置
  const productionTrendOption = {
    title: {
      text: '生产趋势',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['计划产量', '实际产量'],
      bottom: 0
    },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '计划产量',
        type: 'line',
        data: [1200, 1320, 1010, 1340, 1290, 1330],
        smooth: true
      },
      {
        name: '实际产量',
        type: 'line',
        data: [1100, 1280, 980, 1300, 1250, 1280],
        smooth: true
      }
    ]
  };

  // 订单状态分布图表配置
  const orderStatusOption = {
    title: {
      text: '订单状态分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'item'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '订单状态',
        type: 'pie',
        radius: '50%',
        data: [
          { value: 35, name: '已完成' },
          { value: 25, name: '生产中' },
          { value: 20, name: '待生产' },
          { value: 15, name: '已取消' },
          { value: 5, name: '延期' }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };

  return (
    <div style={{ padding: '24px' }}>
      <h1 className="page-title">PMC生产管理仪表盘</h1>
      
      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总订单数"
              value={156}
              prefix={<ShoppingCartOutlined />}
              valueStyle={{ color: '#3f8600' }}
              suffix={<ArrowUpOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="生产计划"
              value={23}
              prefix={<ScheduleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="库存预警"
              value={8}
              prefix={<InboxOutlined />}
              valueStyle={{ color: '#cf1322' }}
              suffix={<ArrowDownOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="完成率"
              value={89.3}
              prefix={<BarChartOutlined />}
              suffix="%"
              precision={1}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 图表区域 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={16}>
          <Card title="生产趋势" className="card-shadow">
            <ReactECharts option={productionTrendOption} style={{ height: 300 }} />
          </Card>
        </Col>
        <Col span={8}>
          <Card title="订单状态分布" className="card-shadow">
            <ReactECharts option={orderStatusOption} style={{ height: 300 }} />
          </Card>
        </Col>
      </Row>

      {/* 最近订单 */}
      <Card title="最近订单" className="card-shadow">
        <Table
          columns={columns}
          dataSource={recentOrders}
          pagination={false}
          size="small"
        />
      </Card>
    </div>
  );
};

export default Dashboard;