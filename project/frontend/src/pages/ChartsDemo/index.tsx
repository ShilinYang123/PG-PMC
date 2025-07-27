import React from 'react';
import { Row, Col, Card, Divider } from 'antd';
import {
  ProductionProgressChart,
  OrderStatusChart,
  EquipmentStatusChart,
  QualityTrendChart,
  MaterialInventoryChart
} from '../../components/Charts';
import type {
  ProductionProgressData,
  OrderStatusData,
  EquipmentStatusData,
  QualityTrendData,
  MaterialInventoryData
} from '../../components/Charts';

const ChartsDemo: React.FC = () => {
  // 模拟生产进度数据
  const productionProgressData: ProductionProgressData[] = [
    {
      orderId: 'ORD001',
      orderName: '智能手机外壳',
      totalQuantity: 1000,
      completedQuantity: 850,
      plannedQuantity: 1000,
      progress: 85,
      status: 'in_progress',
      startDate: '2024-01-15',
      endDate: '2024-02-15'
    },
    {
      orderId: 'ORD002',
      orderName: '电脑主板',
      totalQuantity: 500,
      completedQuantity: 500,
      plannedQuantity: 500,
      progress: 100,
      status: 'completed',
      startDate: '2024-01-10',
      endDate: '2024-02-10'
    },
    {
      orderId: 'ORD003',
      orderName: '汽车零件',
      totalQuantity: 2000,
      completedQuantity: 1200,
      plannedQuantity: 2000,
      progress: 60,
      status: 'delayed',
      startDate: '2024-01-20',
      endDate: '2024-02-20'
    },
    {
      orderId: 'ORD004',
      orderName: '家电配件',
      totalQuantity: 800,
      completedQuantity: 0,
      plannedQuantity: 800,
      progress: 0,
      status: 'pending',
      startDate: '2024-02-01',
      endDate: '2024-03-01'
    }
  ];

  // 模拟订单状态数据
  const orderStatusData: OrderStatusData[] = [
    { status: 'pending', count: 15, percentage: 15, color: '#8c8c8c' },
    { status: 'confirmed', count: 25, percentage: 25, color: '#1890ff' },
    { status: 'in_production', count: 30, percentage: 30, color: '#faad14' },
    { status: 'quality_check', count: 12, percentage: 12, color: '#722ed1' },
    { status: 'completed', count: 18, percentage: 18, color: '#52c41a' }
  ];

  // 模拟设备状态数据
  const equipmentStatusData: EquipmentStatusData[] = [
    {
      equipmentId: 'EQ001',
      equipmentName: '注塑机A',
      status: 'running',
      utilization: 92,
      lastMaintenance: '2024-01-15',
      nextMaintenance: '2024-04-15'
    },
    {
      equipmentId: 'EQ002',
      equipmentName: '冲压机B',
      status: 'running',
      utilization: 78,
      lastMaintenance: '2024-01-10',
      nextMaintenance: '2024-04-10'
    },
    {
      equipmentId: 'EQ003',
      equipmentName: '焊接机C',
      status: 'maintenance',
      utilization: 0,
      lastMaintenance: '2024-01-25',
      nextMaintenance: '2024-04-25'
    },
    {
      equipmentId: 'EQ004',
      equipmentName: '包装机D',
      status: 'error',
      utilization: 0,
      lastMaintenance: '2024-01-20',
      nextMaintenance: '2024-04-20'
    },
    {
      equipmentId: 'EQ005',
      equipmentName: '检测机E',
      status: 'idle',
      utilization: 45,
      lastMaintenance: '2024-01-12',
      nextMaintenance: '2024-04-12'
    }
  ];

  // 模拟质量趋势数据
  const qualityTrendData: QualityTrendData[] = [
    { date: '2024-01-01', passRate: 96.5, defectRate: 2.8, reworkRate: 0.7, totalInspected: 1200 },
    { date: '2024-01-02', passRate: 97.2, defectRate: 2.1, reworkRate: 0.7, totalInspected: 1150 },
    { date: '2024-01-03', passRate: 95.8, defectRate: 3.2, reworkRate: 1.0, totalInspected: 1300 },
    { date: '2024-01-04', passRate: 98.1, defectRate: 1.5, reworkRate: 0.4, totalInspected: 1100 },
    { date: '2024-01-05', passRate: 96.9, defectRate: 2.4, reworkRate: 0.7, totalInspected: 1250 },
    { date: '2024-01-06', passRate: 97.5, defectRate: 1.8, reworkRate: 0.7, totalInspected: 1180 },
    { date: '2024-01-07', passRate: 95.2, defectRate: 3.8, reworkRate: 1.0, totalInspected: 1320 }
  ];

  // 模拟物料库存数据
  const materialInventoryData: MaterialInventoryData[] = [
    {
      materialId: 'MAT001',
      materialName: '钢材',
      currentStock: 150,
      minStock: 100,
      maxStock: 500,
      unit: '吨',
      status: 'normal'
    },
    {
      materialId: 'MAT002',
      materialName: '塑料颗粒',
      currentStock: 80,
      minStock: 100,
      maxStock: 300,
      unit: '公斤',
      status: 'low'
    },
    {
      materialId: 'MAT003',
      materialName: '电子元件',
      currentStock: 45,
      minStock: 50,
      maxStock: 200,
      unit: '个',
      status: 'critical'
    },
    {
      materialId: 'MAT004',
      materialName: '包装材料',
      currentStock: 280,
      minStock: 100,
      maxStock: 250,
      unit: '套',
      status: 'overstock'
    },
    {
      materialId: 'MAT005',
      materialName: '润滑油',
      currentStock: 120,
      minStock: 80,
      maxStock: 200,
      unit: '升',
      status: 'normal'
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card title="图表组件演示" style={{ marginBottom: 24 }}>
        <p>本页面展示了PMC系统中所有可用的图表组件，包括生产进度、订单状态、设备监控、质量趋势和物料库存等。</p>
      </Card>

      <Divider orientation="left">生产管理图表</Divider>
      
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <ProductionProgressChart 
            data={productionProgressData}
            config={{ height: 350 }}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <OrderStatusChart 
            data={orderStatusData}
            config={{ height: 350 }}
          />
        </Col>
        <Col span={12}>
          <QualityTrendChart 
            data={qualityTrendData}
            config={{ height: 350 }}
          />
        </Col>
      </Row>

      <Divider orientation="left">设备与物料管理</Divider>
      
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <EquipmentStatusChart 
            data={equipmentStatusData}
            config={{ height: 350 }}
          />
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <MaterialInventoryChart 
            data={materialInventoryData}
            config={{ height: 350 }}
          />
        </Col>
      </Row>
    </div>
  );
};

export default ChartsDemo;