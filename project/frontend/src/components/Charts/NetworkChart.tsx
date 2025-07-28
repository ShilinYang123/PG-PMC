import React, { useState, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Space, Button, Select, Slider, Tag, Row, Col } from 'antd';
import { ExpandOutlined, CompressOutlined, ReloadOutlined } from '@ant-design/icons';
import { CHART_COLORS } from './types';

const { Option } = Select;

interface NetworkNode {
  id: string;
  name: string;
  value?: number;
  category?: string;
  symbolSize?: number;
  itemStyle?: {
    color?: string;
  };
  label?: {
    show?: boolean;
    position?: string;
  };
}

interface NetworkLink {
  source: string;
  target: string;
  value?: number;
  lineStyle?: {
    color?: string;
    width?: number;
    type?: 'solid' | 'dashed' | 'dotted';
  };
  label?: {
    show?: boolean;
    formatter?: string;
  };
}

interface NetworkCategory {
  name: string;
  itemStyle?: {
    color?: string;
  };
}

interface NetworkChartProps {
  nodes: NetworkNode[];
  links: NetworkLink[];
  categories?: NetworkCategory[];
  title?: string;
  height?: number;
  layout?: 'force' | 'circular' | 'none';
  roam?: boolean;
  focusNodeAdjacency?: boolean;
  showLabels?: boolean;
  repulsion?: number;
  gravity?: number;
}

const NetworkChart: React.FC<NetworkChartProps> = ({
  nodes,
  links,
  categories = [],
  title = '网络关系图',
  height = 600,
  layout = 'force',
  roam = true,
  focusNodeAdjacency = true,
  showLabels = true,
  repulsion = 50,
  gravity = 0.2
}) => {
  const [currentLayout, setCurrentLayout] = useState(layout);
  const [currentRepulsion, setCurrentRepulsion] = useState(repulsion);
  const [currentGravity, setCurrentGravity] = useState(gravity);
  const [labelsVisible, setLabelsVisible] = useState(showLabels);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const chartRef = useRef<any>(null);

  // 处理节点数据
  const processNodes = () => {
    return nodes.map(node => ({
      ...node,
      symbolSize: node.symbolSize || (node.value ? Math.sqrt(node.value) * 2 + 10 : 20),
      itemStyle: {
        color: node.itemStyle?.color || getNodeColor(node.category),
        ...node.itemStyle
      },
      label: {
        show: labelsVisible,
        position: 'right',
        formatter: '{b}',
        fontSize: 12,
        ...node.label
      }
    }));
  };

  // 处理连接数据
  const processLinks = () => {
    return links.map(link => ({
      ...link,
      lineStyle: {
        color: '#aaa',
        width: link.value ? Math.sqrt(link.value) + 1 : 1,
        opacity: 0.6,
        ...link.lineStyle
      },
      label: {
        show: false,
        formatter: link.value ? `{c}` : '',
        fontSize: 10,
        ...link.label
      }
    }));
  };

  // 获取节点颜色
  const getNodeColor = (category?: string) => {
    if (!category) return CHART_COLORS.primary;
    
    const categoryIndex = categories.findIndex(cat => cat.name === category);
    if (categoryIndex >= 0 && categories[categoryIndex].itemStyle?.color) {
      return categories[categoryIndex].itemStyle!.color;
    }
    
    const colors = [
      CHART_COLORS.primary,
      CHART_COLORS.success,
      CHART_COLORS.warning,
      CHART_COLORS.error,
      CHART_COLORS.info,
      CHART_COLORS.purple,
      CHART_COLORS.orange
    ];
    
    return colors[categoryIndex % colors.length] || CHART_COLORS.primary;
  };

  // 获取图表配置
  const getOption = () => {
    const processedNodes = processNodes();
    const processedLinks = processLinks();
    
    return {
      title: {
        text: title,
        left: 'center',
        textStyle: {
          fontSize: 16,
          fontWeight: 'bold'
        }
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            return `节点: ${params.name}<br/>类别: ${params.data.category || '未分类'}<br/>值: ${params.data.value || 'N/A'}`;
          } else if (params.dataType === 'edge') {
            return `连接: ${params.data.source} → ${params.data.target}<br/>权重: ${params.data.value || 'N/A'}`;
          }
          return params.name;
        }
      },
      legend: categories.length > 0 ? {
        data: categories.map(cat => cat.name),
        top: 30,
        itemGap: 20
      } : undefined,
      series: [
        {
          type: 'graph',
          layout: currentLayout,
          data: processedNodes,
          links: processedLinks,
          categories: categories,
          roam: roam,
          focusNodeAdjacency: focusNodeAdjacency,
          draggable: true,
          symbol: 'circle',
          symbolSize: 20,
          lineStyle: {
            color: 'source',
            curveness: 0.1
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 3
            },
            itemStyle: {
              borderColor: '#333',
              borderWidth: 2
            }
          },
          force: currentLayout === 'force' ? {
            repulsion: currentRepulsion,
            gravity: currentGravity,
            edgeLength: [50, 200],
            layoutAnimation: true
          } : undefined,
          circular: currentLayout === 'circular' ? {
            rotateLabel: true
          } : undefined,
          animationDuration: 1500,
          animationEasingUpdate: 'quinticInOut'
        }
      ]
    };
  };

  // 重置图表
  const resetChart = () => {
    if (chartRef.current) {
      const chartInstance = chartRef.current.getEchartsInstance();
      chartInstance.setOption(getOption(), true);
    }
  };

  // 图表事件处理
  const onEvents = {
    click: (params: any) => {
      if (params.dataType === 'node') {
        setSelectedNode(params.data.id);
      }
    }
  };

  // 计算网络统计信息
  const getNetworkStats = () => {
    const nodeCount = nodes.length;
    const linkCount = links.length;
    const categoryCount = categories.length;
    const density = nodeCount > 1 ? (2 * linkCount) / (nodeCount * (nodeCount - 1)) : 0;
    
    return {
      nodeCount,
      linkCount,
      categoryCount,
      density: parseFloat((density * 100).toFixed(2))
    };
  };

  const stats = getNetworkStats();

  return (
    <Card 
      title={title} 
      style={{ height: height + 180 }}
      extra={
        <Space>
          <Tag color="blue">节点: {stats.nodeCount}</Tag>
          <Tag color="green">连接: {stats.linkCount}</Tag>
          <Tag color="orange">类别: {stats.categoryCount}</Tag>
          <Tag color="purple">密度: {stats.density}%</Tag>
        </Space>
      }
    >
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Space>
            <span>布局:</span>
            <Select
              value={currentLayout}
              onChange={setCurrentLayout}
              style={{ width: 100 }}
            >
              <Option value="force">力导向</Option>
              <Option value="circular">环形</Option>
              <Option value="none">固定</Option>
            </Select>
          </Space>
        </Col>
        <Col span={6}>
          <Space>
            <span>斥力:</span>
            <Slider
              min={10}
              max={200}
              value={currentRepulsion}
              onChange={setCurrentRepulsion}
              style={{ width: 100 }}
              disabled={currentLayout !== 'force'}
            />
          </Space>
        </Col>
        <Col span={6}>
          <Space>
            <span>引力:</span>
            <Slider
              min={0.1}
              max={1}
              step={0.1}
              value={currentGravity}
              onChange={setCurrentGravity}
              style={{ width: 100 }}
              disabled={currentLayout !== 'force'}
            />
          </Space>
        </Col>
        <Col span={6}>
          <Space>
            <Button
              icon={labelsVisible ? <CompressOutlined /> : <ExpandOutlined />}
              onClick={() => setLabelsVisible(!labelsVisible)}
            >
              {labelsVisible ? '隐藏标签' : '显示标签'}
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={resetChart}
            >
              重置
            </Button>
          </Space>
        </Col>
      </Row>
      
      {selectedNode && (
        <div style={{ marginBottom: 16, padding: 8, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
          <strong>选中节点:</strong> {selectedNode}
        </div>
      )}
      
      <ReactECharts
        ref={chartRef}
        option={getOption()}
        style={{ height: height, width: '100%' }}
        notMerge={true}
        lazyUpdate={true}
        onEvents={onEvents}
      />
    </Card>
  );
};

export default NetworkChart;
export type { NetworkNode, NetworkLink, NetworkCategory, NetworkChartProps };