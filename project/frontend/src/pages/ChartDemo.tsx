import React, { useState } from 'react';
import { Card, Row, Col, Tabs, Space, Button, message } from 'antd';
import {
  ProductionProgressChart,
  OrderStatusChart,
  EquipmentStatusChart,
  QualityTrendChart,
  MaterialInventoryChart,
  DashboardChart,
  RadarChart,
  HeatmapChart,
  MultiAxisChart,
  RealTimeChart
} from '../components/Charts';
import type {
  ProductionProgressData,
  OrderStatusData,
  EquipmentStatusData,
  QualityTrendData,
  MaterialInventoryData,
  DashboardData,
  RadarDataItem,
  RadarIndicator,
  HeatmapDataItem,
  SeriesData,
  YAxisConfig
} from '../components/Charts';

const ChartDemo: React.FC = () => {
  // 模拟数据
  const productionData: ProductionProgressData[] = [
    {
      orderId: 'ORD001',
      orderName: '汽车零件A',
      totalQuantity: 1000,
      completedQuantity: 850,
      plannedQuantity: 1000,
      progress: 85,
      status: 'in_progress',
      startDate: '2024-01-01',
      endDate: '2024-01-15'
    },
    {
      orderId: 'ORD002',
      orderName: '电子元件B',
      totalQuantity: 500,
      completedQuantity: 500,
      plannedQuantity: 500,
      progress: 100,
      status: 'completed',
      startDate: '2024-01-05',
      endDate: '2024-01-20'
    }
  ];

  const orderData: OrderStatusData[] = [
    { status: 'pending', count: 15, percentage: 12.5, color: '#faad14' },
    { status: 'confirmed', count: 25, percentage: 20.8, color: '#1890ff' },
    { status: 'in_production', count: 40, percentage: 33.3, color: '#52c41a' },
    { status: 'quality_check', count: 20, percentage: 16.7, color: '#722ed1' },
    { status: 'completed', count: 15, percentage: 12.5, color: '#13c2c2' },
    { status: 'shipped', count: 5, percentage: 4.2, color: '#eb2f96' }
  ];

  const equipmentData: EquipmentStatusData[] = [
    {
      equipmentId: 'EQ001',
      equipmentName: '数控机床1',
      status: 'running',
      utilization: 85,
      lastMaintenance: '2024-01-01',
      nextMaintenance: '2024-02-01'
    },
    {
      equipmentId: 'EQ002',
      equipmentName: '注塑机2',
      status: 'idle',
      utilization: 45,
      lastMaintenance: '2024-01-05',
      nextMaintenance: '2024-02-05'
    }
  ];

  const qualityData: QualityTrendData[] = [
    {
      date: '2024-01-01',
      passRate: 95.5,
      defectRate: 3.2,
      reworkRate: 1.3,
      totalInspected: 1000
    },
    {
      date: '2024-01-02',
      passRate: 96.2,
      defectRate: 2.8,
      reworkRate: 1.0,
      totalInspected: 1200
    }
  ];

  const materialData: MaterialInventoryData[] = [
    {
      materialId: 'MAT001',
      materialName: '钢材A',
      currentStock: 150,
      minStock: 100,
      maxStock: 500,
      unit: 'kg',
      status: 'normal'
    },
    {
      materialId: 'MAT002',
      materialName: '塑料B',
      currentStock: 50,
      minStock: 80,
      maxStock: 300,
      unit: 'kg',
      status: 'low'
    }
  ];

  const dashboardData: DashboardData[] = [
    {
      title: '生产效率',
      value: 85,
      max: 100,
      unit: '%',
      status: 'normal',
      trend: 5.2
    },
    {
      title: '设备利用率',
      value: 78,
      max: 100,
      unit: '%',
      status: 'warning',
      trend: -2.1
    },
    {
      title: '质量合格率',
      value: 96,
      max: 100,
      unit: '%',
      status: 'normal',
      trend: 1.5
    },
    {
      title: '能耗指标',
      value: 120,
      max: 150,
      unit: 'kWh',
      status: 'critical',
      trend: 8.3
    }
  ];

  const radarData: RadarDataItem[] = [
    {
      name: '产品A',
      values: [85, 92, 78, 88, 95],
      color: '#1890ff'
    },
    {
      name: '产品B',
      values: [78, 85, 92, 82, 88],
      color: '#52c41a'
    }
  ];

  const radarIndicators: RadarIndicator[] = [
    { name: '质量', max: 100, unit: '%' },
    { name: '效率', max: 100, unit: '%' },
    { name: '成本', max: 100, unit: '%' },
    { name: '交期', max: 100, unit: '%' },
    { name: '创新', max: 100, unit: '%' }
  ];

  const heatmapData: HeatmapDataItem[] = [
    { date: '2024-01-01', hour: 8, value: 45 },
    { date: '2024-01-01', hour: 9, value: 62 },
    { date: '2024-01-01', hour: 10, value: 78 },
    { date: '2024-01-02', hour: 8, value: 52 },
    { date: '2024-01-02', hour: 9, value: 68 },
    { date: '2024-01-02', hour: 10, value: 85 }
  ];

  const multiAxisXData = ['1月', '2月', '3月', '4月', '5月', '6月'];
  const multiAxisSeries: SeriesData[] = [
    {
      name: '生产量',
      data: [120, 132, 101, 134, 90, 230],
      type: 'bar',
      yAxisIndex: 0,
      color: '#1890ff',
      unit: '件'
    },
    {
      name: '效率',
      data: [85, 88, 82, 90, 78, 92],
      type: 'line',
      yAxisIndex: 1,
      color: '#52c41a',
      unit: '%',
      smooth: true
    }
  ];

  const multiAxisYAxes: YAxisConfig[] = [
    {
      name: '生产量',
      unit: '件',
      position: 'left',
      color: '#1890ff'
    },
    {
      name: '效率',
      unit: '%',
      position: 'right',
      color: '#52c41a'
    }
  ];

  const tabItems = [
    {
      key: 'basic',
      label: '基础图表',
      children: (
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <ProductionProgressChart data={productionData} />
          </Col>
          <Col span={12}>
            <OrderStatusChart data={orderData} />
          </Col>
          <Col span={12}>
            <EquipmentStatusChart data={equipmentData} />
          </Col>
          <Col span={12}>
            <QualityTrendChart data={qualityData} />
          </Col>
          <Col span={24}>
            <MaterialInventoryChart data={materialData} />
          </Col>
        </Row>
      )
    },
    {
      key: 'advanced',
      label: '高级图表',
      children: (
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <DashboardChart data={dashboardData} />
          </Col>
          <Col span={12}>
            <RadarChart 
              data={radarData} 
              indicators={radarIndicators}
              title="产品综合评价"
            />
          </Col>
          <Col span={12}>
            <HeatmapChart 
              data={heatmapData}
              title="生产热力图"
              valueUnit="件"
            />
          </Col>
          <Col span={24}>
            <MultiAxisChart
              xAxisData={multiAxisXData}
              series={multiAxisSeries}
              yAxes={multiAxisYAxes}
              title="生产量与效率对比"
            />
          </Col>
        </Row>
      )
    },
    {
      key: 'realtime',
      label: '实时监控',
      children: (
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <RealTimeChart
              title="实时生产监控"
              unit="件/小时"
              thresholds={{
                warning: 70,
                error: 90
              }}
              maxDataPoints={30}
              updateInterval={3000}
            />
          </Col>
        </Row>
      )
    }
  ];

  const handleExportData = () => {
    message.success('数据导出功能开发中...');
  };

  const handleRefreshData = () => {
    message.success('数据已刷新');
  };

  return (
    <div style={{ padding: '24px' }}>
      <Card 
        title="图表组件演示" 
        extra={
          <Space>
            <Button onClick={handleRefreshData}>刷新数据</Button>
            <Button type="primary" onClick={handleExportData}>导出数据</Button>
          </Space>
        }
      >
        <Tabs items={tabItems} defaultActiveKey="basic" />
      </Card>
    </div>
  );
};

export default ChartDemo;