import React, { useState } from 'react';
import { Card, Row, Col, Tabs, Space, Button, message } from 'antd';
import {
  Map3DChart,
  TimeSeriesChart,
  Bar3DChart,
  NetworkChart,
  SankeyChart,
  FunnelChart
} from '../../components/Charts';
import type {
  Map3DDataItem,
  TimeSeriesDataPoint,
  Bar3DDataItem,
  NetworkNode,
  NetworkLink,
  NetworkCategory,
  SankeyNode,
  SankeyLink,
  FunnelDataItem
} from '../../components/Charts';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';

const { TabPane } = Tabs;

const AdvancedChartsDemo: React.FC = () => {
  const [activeTab, setActiveTab] = useState('map3d');

  // 3D地图数据
  const map3DData: Map3DDataItem[] = [
    { name: '北京', value: [116.46, 39.92, 2100] },
    { name: '上海', value: [121.48, 31.22, 1800] },
    { name: '广州', value: [113.23, 23.16, 1500] },
    { name: '深圳', value: [114.07, 22.62, 1600] },
    { name: '杭州', value: [120.19, 30.26, 1200] },
    { name: '成都', value: [104.06, 30.67, 1100] },
    { name: '西安', value: [108.95, 34.27, 900] },
    { name: '武汉', value: [114.31, 30.52, 1000] }
  ];

  // 时间序列数据
  const timeSeriesData: TimeSeriesDataPoint[] = [
    { timestamp: '2024-01-01', value: 120 },
    { timestamp: '2024-01-02', value: 132 },
    { timestamp: '2024-01-03', value: 101 },
    { timestamp: '2024-01-04', value: 134 },
    { timestamp: '2024-01-05', value: 90 },
    { timestamp: '2024-01-06', value: 230 },
    { timestamp: '2024-01-07', value: 210 },
    { timestamp: '2024-01-08', value: 220 },
    { timestamp: '2024-01-09', value: 180 },
    { timestamp: '2024-01-10', value: 200 },
    { timestamp: '2024-01-11', value: 190 },
    { timestamp: '2024-01-12', value: 240 },
    { timestamp: '2024-01-13', value: 250 },
    { timestamp: '2024-01-14', value: 260 },
    { timestamp: '2024-01-15', value: 270 }
  ];

  // 3D柱状图数据
  const bar3DData: Bar3DDataItem[] = [
    { name: '产品A', value: 320, category: '电子产品' },
    { name: '产品B', value: 240, category: '机械设备' },
    { name: '产品C', value: 180, category: '化工原料' },
    { name: '产品D', value: 290, category: '电子产品' },
    { name: '产品E', value: 150, category: '纺织品' },
    { name: '产品F', value: 200, category: '食品' },
    { name: '产品G', value: 160, category: '医药' },
    { name: '产品H', value: 220, category: '汽车配件' }
  ];

  // 网络图数据
  const networkNodes: NetworkNode[] = [
    { id: '1', name: '生产计划', category: '核心模块', value: 100 },
    { id: '2', name: '物料管理', category: '核心模块', value: 80 },
    { id: '3', name: '质量控制', category: '核心模块', value: 90 },
    { id: '4', name: '设备管理', category: '支持模块', value: 70 },
    { id: '5', name: '人员管理', category: '支持模块', value: 60 },
    { id: '6', name: '成本控制', category: '管理模块', value: 85 },
    { id: '7', name: '数据分析', category: '管理模块', value: 95 },
    { id: '8', name: '报表系统', category: '管理模块', value: 75 }
  ];

  const networkLinks: NetworkLink[] = [
    { source: '1', target: '2', value: 10 },
    { source: '1', target: '3', value: 8 },
    { source: '2', target: '4', value: 6 },
    { source: '3', target: '4', value: 7 },
    { source: '4', target: '5', value: 5 },
    { source: '1', target: '6', value: 9 },
    { source: '6', target: '7', value: 8 },
    { source: '7', target: '8', value: 6 },
    { source: '3', target: '7', value: 7 },
    { source: '2', target: '6', value: 5 }
  ];

  const networkCategories: NetworkCategory[] = [
    { name: '核心模块', itemStyle: { color: '#1890ff' } },
    { name: '支持模块', itemStyle: { color: '#52c41a' } },
    { name: '管理模块', itemStyle: { color: '#faad14' } }
  ];

  // 桑基图数据
  const sankeyNodes: SankeyNode[] = [
    { name: '原材料A', value: 1000 },
    { name: '原材料B', value: 800 },
    { name: '原材料C', value: 600 },
    { name: '半成品X', value: 900 },
    { name: '半成品Y', value: 700 },
    { name: '成品1', value: 500 },
    { name: '成品2', value: 400 },
    { name: '成品3', value: 300 }
  ];

  const sankeyLinks: SankeyLink[] = [
    { source: '原材料A', target: '半成品X', value: 600 },
    { source: '原材料A', target: '半成品Y', value: 400 },
    { source: '原材料B', target: '半成品X', value: 300 },
    { source: '原材料B', target: '半成品Y', value: 300 },
    { source: '原材料C', target: '半成品Y', value: 200 },
    { source: '半成品X', target: '成品1', value: 500 },
    { source: '半成品X', target: '成品2', value: 400 },
    { source: '半成品Y', target: '成品2', value: 200 },
    { source: '半成品Y', target: '成品3', value: 300 }
  ];

  // 漏斗图数据
  const funnelData: FunnelDataItem[] = [
    { name: '访问量', value: 10000 },
    { name: '浏览量', value: 8000 },
    { name: '咨询量', value: 3000 },
    { name: '试用量', value: 1500 },
    { name: '购买量', value: 800 },
    { name: '复购量', value: 400 }
  ];

  // 导出图表
  const exportChart = (chartType: string) => {
    message.success(`${chartType}图表导出功能开发中...`);
  };

  // 刷新数据
  const refreshData = () => {
    message.success('数据已刷新');
  };

  const tabItems = [
    {
      key: 'map3d',
      label: '3D地图',
      children: (
        <Map3DChart
          data={map3DData}
          title="全国生产基地分布"
          height={500}
          mapType="china"
        />
      )
    },
    {
      key: 'timeseries',
      label: '时间序列',
      children: (
        <TimeSeriesChart
          data={timeSeriesData}
          title="生产数据时间序列分析"
          height={400}
          showTrend={true}
          showForecast={true}
          forecastPeriods={5}
        />
      )
    },
    {
      key: 'bar3d',
      label: '3D柱状图',
      children: (
        <Bar3DChart
          data={bar3DData}
          title="产品销量3D对比"
          height={500}
          viewAngle={{ alpha: 40, beta: 40 }}
        />
      )
    },
    {
      key: 'network',
      label: '网络关系图',
      children: (
        <NetworkChart
          nodes={networkNodes}
          links={networkLinks}
          categories={networkCategories}
          title="系统模块关系图"
          height={600}
          layout="force"
          focusNodeAdjacency={true}
        />
      )
    },
    {
      key: 'sankey',
      label: '桑基图',
      children: (
        <SankeyChart
          nodes={sankeyNodes}
          links={sankeyLinks}
          title="生产流程桑基图"
          height={500}
          orient="horizontal"
          showValues={true}
        />
      )
    },
    {
      key: 'funnel',
      label: '漏斗图',
      children: (
        <FunnelChart
          data={funnelData}
          title="销售转化漏斗"
          height={500}
          sort="descending"
          showPercentages={true}
        />
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="高级图表组件演示"
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={refreshData}
            >
              刷新数据
            </Button>
            <Button
              icon={<DownloadOutlined />}
              onClick={() => exportChart(activeTab)}
            >
              导出图表
            </Button>
          </Space>
        }
      >
        <div style={{ marginBottom: 16 }}>
          <p style={{ color: '#666', margin: 0 }}>
            本页面展示了基于ECharts的高级图表组件，包括3D可视化、时间序列分析、网络关系图等。
            所有图表都支持交互操作、数据导出和实时更新。
          </p>
        </div>
        
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
          size="large"
          tabBarStyle={{ marginBottom: 24 }}
        />
      </Card>
      
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={8}>
          <Card title="图表特性" size="small">
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>支持3D可视化效果</li>
              <li>丰富的交互操作</li>
              <li>实时数据更新</li>
              <li>多种布局算法</li>
              <li>自定义样式主题</li>
            </ul>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="技术栈" size="small">
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>ECharts 5.x</li>
              <li>ECharts-GL (3D支持)</li>
              <li>React + TypeScript</li>
              <li>Ant Design</li>
              <li>echarts-for-react</li>
            </ul>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="应用场景" size="small">
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>生产数据监控</li>
              <li>业务流程分析</li>
              <li>地理信息展示</li>
              <li>关系网络分析</li>
              <li>转化率分析</li>
            </ul>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default AdvancedChartsDemo;