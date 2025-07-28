import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Space, Button, Select, Switch, Tag, Row, Col } from 'antd';
import { SettingOutlined, FullscreenOutlined } from '@ant-design/icons';
import { CHART_COLORS } from './types';

const { Option } = Select;

interface SankeyNode {
  name: string;
  value?: number;
  depth?: number;
  itemStyle?: {
    color?: string;
  };
  label?: {
    show?: boolean;
    position?: string;
    formatter?: string;
  };
}

interface SankeyLink {
  source: string;
  target: string;
  value: number;
  lineStyle?: {
    color?: string;
    opacity?: number;
  };
}

interface SankeyChartProps {
  nodes: SankeyNode[];
  links: SankeyLink[];
  title?: string;
  height?: number;
  orient?: 'horizontal' | 'vertical';
  nodeAlign?: 'justify' | 'left' | 'right';
  nodeGap?: number;
  nodeWidth?: number;
  showValues?: boolean;
  colorScheme?: 'default' | 'gradient' | 'category';
}

const SankeyChart: React.FC<SankeyChartProps> = ({
  nodes,
  links,
  title = '桑基图',
  height = 500,
  orient = 'horizontal',
  nodeAlign = 'justify',
  nodeGap = 8,
  nodeWidth = 20,
  showValues = true,
  colorScheme = 'default'
}) => {
  const [currentOrient, setCurrentOrient] = useState(orient);
  const [currentNodeAlign, setCurrentNodeAlign] = useState(nodeAlign);
  const [currentNodeGap, setCurrentNodeGap] = useState(nodeGap);
  const [currentNodeWidth, setCurrentNodeWidth] = useState(nodeWidth);
  const [valuesVisible, setValuesVisible] = useState(showValues);
  const [currentColorScheme, setCurrentColorScheme] = useState(colorScheme);

  // 获取颜色方案
  const getColorScheme = () => {
    switch (currentColorScheme) {
      case 'gradient':
        return {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 1,
          y2: 0,
          colorStops: [
            { offset: 0, color: CHART_COLORS.primary },
            { offset: 0.5, color: CHART_COLORS.info },
            { offset: 1, color: CHART_COLORS.success }
          ]
        };
      case 'category':
        return [
          CHART_COLORS.primary,
          CHART_COLORS.success,
          CHART_COLORS.warning,
          CHART_COLORS.error,
          CHART_COLORS.info,
          CHART_COLORS.purple,
          CHART_COLORS.orange
        ];
      default:
        return CHART_COLORS.primary;
    }
  };

  // 处理节点数据
  const processNodes = () => {
    return nodes.map((node, index) => {
      let nodeColor;
      
      if (currentColorScheme === 'category') {
        const colors = getColorScheme() as string[];
        nodeColor = colors[index % colors.length];
      } else if (currentColorScheme === 'gradient') {
        nodeColor = getColorScheme();
      } else {
        nodeColor = node.itemStyle?.color || CHART_COLORS.primary;
      }
      
      return {
        ...node,
        itemStyle: {
          color: nodeColor,
          borderColor: '#fff',
          borderWidth: 1,
          ...node.itemStyle
        },
        label: {
          show: true,
          position: currentOrient === 'horizontal' ? 'right' : 'top',
          formatter: valuesVisible && node.value ? `{b}\n{c}` : '{b}',
          fontSize: 12,
          fontWeight: 'bold',
          ...node.label
        }
      };
    });
  };

  // 处理连接数据
  const processLinks = () => {
    return links.map(link => ({
      ...link,
      lineStyle: {
        opacity: 0.6,
        curveness: 0.5,
        ...link.lineStyle
      },
      emphasis: {
        lineStyle: {
          opacity: 0.8
        }
      }
    }));
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
        triggerOn: 'mousemove',
        formatter: (params: any) => {
          if (params.dataType === 'node') {
            return `节点: ${params.name}<br/>值: ${params.value || 'N/A'}`;
          } else if (params.dataType === 'edge') {
            return `${params.data.source} → ${params.data.target}<br/>流量: ${params.data.value}`;
          }
          return params.name;
        }
      },
      series: [
        {
          type: 'sankey',
          data: processedNodes,
          links: processedLinks,
          orient: currentOrient,
          nodeAlign: currentNodeAlign,
          nodeGap: currentNodeGap,
          nodeWidth: currentNodeWidth,
          layoutIterations: 32,
          focusNodeAdjacency: 'allEdges',
          itemStyle: {
            borderWidth: 1,
            borderColor: '#aaa'
          },
          lineStyle: {
            color: 'gradient',
            curveness: 0.5
          },
          emphasis: {
            focus: 'adjacency',
            itemStyle: {
              borderColor: '#333',
              borderWidth: 2
            },
            lineStyle: {
              opacity: 0.8
            }
          },
          animationDuration: 1000,
          animationEasing: 'cubicInOut'
        }
      ]
    };
  };

  // 计算桑基图统计信息
  const getSankeyStats = () => {
    const nodeCount = nodes.length;
    const linkCount = links.length;
    const totalFlow = links.reduce((sum, link) => sum + link.value, 0);
    const maxFlow = Math.max(...links.map(link => link.value));
    const minFlow = Math.min(...links.map(link => link.value));
    const avgFlow = totalFlow / linkCount;
    
    // 计算层级数
    const depths = nodes.map(node => node.depth || 0);
    const maxDepth = Math.max(...depths);
    const levels = maxDepth + 1;
    
    return {
      nodeCount,
      linkCount,
      totalFlow,
      maxFlow,
      minFlow,
      avgFlow: parseFloat(avgFlow.toFixed(2)),
      levels
    };
  };

  const stats = getSankeyStats();

  return (
    <Card 
      title={title} 
      style={{ height: height + 200 }}
      extra={
        <Space>
          <Tag color="blue">节点: {stats.nodeCount}</Tag>
          <Tag color="green">连接: {stats.linkCount}</Tag>
          <Tag color="orange">层级: {stats.levels}</Tag>
          <Tag color="purple">总流量: {stats.totalFlow}</Tag>
        </Space>
      }
    >
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Space direction="vertical" size="small">
            <span>方向:</span>
            <Select
              value={currentOrient}
              onChange={setCurrentOrient}
              style={{ width: '100%' }}
            >
              <Option value="horizontal">水平</Option>
              <Option value="vertical">垂直</Option>
            </Select>
          </Space>
        </Col>
        <Col span={4}>
          <Space direction="vertical" size="small">
            <span>对齐:</span>
            <Select
              value={currentNodeAlign}
              onChange={setCurrentNodeAlign}
              style={{ width: '100%' }}
            >
              <Option value="justify">两端对齐</Option>
              <Option value="left">左对齐</Option>
              <Option value="right">右对齐</Option>
            </Select>
          </Space>
        </Col>
        <Col span={4}>
          <Space direction="vertical" size="small">
            <span>颜色方案:</span>
            <Select
              value={currentColorScheme}
              onChange={setCurrentColorScheme}
              style={{ width: '100%' }}
            >
              <Option value="default">默认</Option>
              <Option value="gradient">渐变</Option>
              <Option value="category">分类</Option>
            </Select>
          </Space>
        </Col>
        <Col span={4}>
          <Space direction="vertical" size="small">
            <span>节点宽度:</span>
            <Select
              value={currentNodeWidth}
              onChange={setCurrentNodeWidth}
              style={{ width: '100%' }}
            >
              <Option value={15}>细</Option>
              <Option value={20}>中</Option>
              <Option value={25}>粗</Option>
              <Option value={30}>很粗</Option>
            </Select>
          </Space>
        </Col>
        <Col span={4}>
          <Space direction="vertical" size="small">
            <span>节点间距:</span>
            <Select
              value={currentNodeGap}
              onChange={setCurrentNodeGap}
              style={{ width: '100%' }}
            >
              <Option value={4}>紧密</Option>
              <Option value={8}>正常</Option>
              <Option value={12}>宽松</Option>
              <Option value={16}>很宽松</Option>
            </Select>
          </Space>
        </Col>
        <Col span={4}>
          <Space direction="vertical" size="small">
            <span>显示数值:</span>
            <Switch
              checked={valuesVisible}
              onChange={setValuesVisible}
              checkedChildren="开"
              unCheckedChildren="关"
            />
          </Space>
        </Col>
      </Row>
      
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: CHART_COLORS.primary }}>
              {stats.totalFlow}
            </div>
            <div style={{ color: '#666' }}>总流量</div>
          </div>
        </Col>
        <Col span={6}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: CHART_COLORS.success }}>
              {stats.maxFlow}
            </div>
            <div style={{ color: '#666' }}>最大流量</div>
          </div>
        </Col>
        <Col span={6}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: CHART_COLORS.warning }}>
              {stats.minFlow}
            </div>
            <div style={{ color: '#666' }}>最小流量</div>
          </div>
        </Col>
        <Col span={6}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: CHART_COLORS.info }}>
              {stats.avgFlow}
            </div>
            <div style={{ color: '#666' }}>平均流量</div>
          </div>
        </Col>
      </Row>
      
      <ReactECharts
        option={getOption()}
        style={{ height: height, width: '100%' }}
        notMerge={true}
        lazyUpdate={true}
      />
    </Card>
  );
};

export default SankeyChart;
export type { SankeyNode, SankeyLink, SankeyChartProps };