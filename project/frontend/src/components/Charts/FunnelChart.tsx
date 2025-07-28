import React, { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Space, Button, Select, Switch, Tag, Row, Col, Statistic } from 'antd';
import { FunnelPlotOutlined, PercentageOutlined } from '@ant-design/icons';
import { CHART_COLORS } from './types';

const { Option } = Select;

interface FunnelDataItem {
  name: string;
  value: number;
  itemStyle?: {
    color?: string;
  };
  label?: {
    show?: boolean;
    position?: string;
    formatter?: string;
  };
}

interface FunnelChartProps {
  data: FunnelDataItem[];
  title?: string;
  height?: number;
  sort?: 'ascending' | 'descending' | 'none';
  funnelAlign?: 'left' | 'center' | 'right';
  gap?: number;
  showLabels?: boolean;
  showValues?: boolean;
  showPercentages?: boolean;
  colorScheme?: 'default' | 'gradient' | 'rainbow';
}

const FunnelChart: React.FC<FunnelChartProps> = ({
  data,
  title = '漏斗图',
  height = 500,
  sort = 'descending',
  funnelAlign = 'center',
  gap = 2,
  showLabels = true,
  showValues = true,
  showPercentages = true,
  colorScheme = 'default'
}) => {
  const [currentSort, setCurrentSort] = useState(sort);
  const [currentAlign, setCurrentAlign] = useState(funnelAlign);
  const [currentGap, setCurrentGap] = useState(gap);
  const [labelsVisible, setLabelsVisible] = useState(showLabels);
  const [valuesVisible, setValuesVisible] = useState(showValues);
  const [percentagesVisible, setPercentagesVisible] = useState(showPercentages);
  const [currentColorScheme, setCurrentColorScheme] = useState(colorScheme);

  // 获取颜色方案
  const getColors = () => {
    switch (currentColorScheme) {
      case 'gradient':
        return data.map((_, index) => {
          const ratio = index / (data.length - 1);
          const r = Math.round(24 + (255 - 24) * ratio);
          const g = Math.round(144 + (99 - 144) * ratio);
          const b = Math.round(255 + (71 - 255) * ratio);
          return `rgb(${r}, ${g}, ${b})`;
        });
      case 'rainbow':
        return [
          CHART_COLORS.error,
          CHART_COLORS.warning,
          CHART_COLORS.primary,
          CHART_COLORS.info,
          CHART_COLORS.success,
          CHART_COLORS.purple,
          CHART_COLORS.orange
        ];
      default:
        return [
          CHART_COLORS.primary,
          CHART_COLORS.success,
          CHART_COLORS.warning,
          CHART_COLORS.error,
          CHART_COLORS.info,
          CHART_COLORS.purple,
          CHART_COLORS.orange
        ];
    }
  };

  // 处理数据排序
  const processData = () => {
    let sortedData = [...data];
    
    if (currentSort === 'ascending') {
      sortedData.sort((a, b) => a.value - b.value);
    } else if (currentSort === 'descending') {
      sortedData.sort((a, b) => b.value - a.value);
    }
    
    const colors = getColors();
    const totalValue = sortedData.reduce((sum, item) => sum + item.value, 0);
    
    return sortedData.map((item, index) => {
      const percentage = totalValue > 0 ? ((item.value / totalValue) * 100).toFixed(1) : '0.0';
      
      let labelFormatter = '';
      if (labelsVisible) {
        labelFormatter += '{b}';
        if (valuesVisible && percentagesVisible) {
          labelFormatter += '\n{c} ({d}%)';
        } else if (valuesVisible) {
          labelFormatter += '\n{c}';
        } else if (percentagesVisible) {
          labelFormatter += '\n{d}%';
        }
      }
      
      return {
        ...item,
        itemStyle: {
          color: item.itemStyle?.color || colors[index % colors.length],
          borderColor: '#fff',
          borderWidth: 1,
          ...item.itemStyle
        },
        label: {
          show: labelsVisible,
          position: 'inside',
          formatter: labelFormatter,
          fontSize: 12,
          fontWeight: 'bold',
          color: '#fff',
          ...item.label
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      };
    });
  };

  // 获取图表配置
  const getOption = () => {
    const processedData = processData();
    
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
          const { name, value, percent } = params;
          return `${name}<br/>数值: ${value}<br/>占比: ${percent}%`;
        }
      },
      legend: {
        orient: 'horizontal',
        left: 'center',
        bottom: 10,
        data: processedData.map(item => item.name)
      },
      series: [
        {
          type: 'funnel',
          data: processedData,
          sort: currentSort,
          funnelAlign: currentAlign,
          gap: currentGap,
          left: '10%',
          right: '10%',
          top: '15%',
          bottom: '15%',
          width: '80%',
          height: '70%',
          minSize: '0%',
          maxSize: '100%',
          itemStyle: {
            borderColor: '#fff',
            borderWidth: 1
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          },
          animationType: 'scale',
          animationEasing: 'elasticOut',
          animationDelay: (idx: number) => idx * 60
        }
      ]
    };
  };

  // 计算转化率
  const getConversionRates = () => {
    const sortedData = processData();
    const rates = [];
    
    for (let i = 1; i < sortedData.length; i++) {
      const currentValue = sortedData[i].value;
      const previousValue = sortedData[i - 1].value;
      const rate = previousValue > 0 ? ((currentValue / previousValue) * 100).toFixed(1) : '0.0';
      
      rates.push({
        from: sortedData[i - 1].name,
        to: sortedData[i].name,
        rate: parseFloat(rate),
        loss: previousValue - currentValue
      });
    }
    
    return rates;
  };

  // 计算统计信息
  const getStats = () => {
    const totalValue = data.reduce((sum, item) => sum + item.value, 0);
    const maxValue = Math.max(...data.map(item => item.value));
    const minValue = Math.min(...data.map(item => item.value));
    const avgValue = totalValue / data.length;
    const overallConversion = maxValue > 0 ? ((minValue / maxValue) * 100).toFixed(1) : '0.0';
    
    return {
      totalValue,
      maxValue,
      minValue,
      avgValue: parseFloat(avgValue.toFixed(2)),
      overallConversion: parseFloat(overallConversion)
    };
  };

  const conversionRates = getConversionRates();
  const stats = getStats();

  return (
    <Card 
      title={title} 
      style={{ height: height + 300 }}
      extra={
        <Space>
          <Tag color="blue">总计: {stats.totalValue}</Tag>
          <Tag color="green">最大: {stats.maxValue}</Tag>
          <Tag color="orange">最小: {stats.minValue}</Tag>
          <Tag color="purple">转化率: {stats.overallConversion}%</Tag>
        </Space>
      }
    >
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={4}>
          <Space direction="vertical" size="small">
            <span>排序:</span>
            <Select
              value={currentSort}
              onChange={setCurrentSort}
              style={{ width: '100%' }}
            >
              <Option value="descending">降序</Option>
              <Option value="ascending">升序</Option>
              <Option value="none">原序</Option>
            </Select>
          </Space>
        </Col>
        <Col span={4}>
          <Space direction="vertical" size="small">
            <span>对齐:</span>
            <Select
              value={currentAlign}
              onChange={setCurrentAlign}
              style={{ width: '100%' }}
            >
              <Option value="center">居中</Option>
              <Option value="left">左对齐</Option>
              <Option value="right">右对齐</Option>
            </Select>
          </Space>
        </Col>
        <Col span={4}>
          <Space direction="vertical" size="small">
            <span>颜色:</span>
            <Select
              value={currentColorScheme}
              onChange={setCurrentColorScheme}
              style={{ width: '100%' }}
            >
              <Option value="default">默认</Option>
              <Option value="gradient">渐变</Option>
              <Option value="rainbow">彩虹</Option>
            </Select>
          </Space>
        </Col>
        <Col span={4}>
          <Space direction="vertical" size="small">
            <span>间距:</span>
            <Select
              value={currentGap}
              onChange={setCurrentGap}
              style={{ width: '100%' }}
            >
              <Option value={0}>无间距</Option>
              <Option value={2}>小间距</Option>
              <Option value={5}>中间距</Option>
              <Option value={10}>大间距</Option>
            </Select>
          </Space>
        </Col>
        <Col span={8}>
          <Space>
            <Switch
              checked={labelsVisible}
              onChange={setLabelsVisible}
              checkedChildren="标签"
              unCheckedChildren="标签"
            />
            <Switch
              checked={valuesVisible}
              onChange={setValuesVisible}
              checkedChildren="数值"
              unCheckedChildren="数值"
            />
            <Switch
              checked={percentagesVisible}
              onChange={setPercentagesVisible}
              checkedChildren="百分比"
              unCheckedChildren="百分比"
            />
          </Space>
        </Col>
      </Row>
      
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Statistic
            title="总数值"
            value={stats.totalValue}
            prefix={<FunnelPlotOutlined />}
            valueStyle={{ color: CHART_COLORS.primary }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="平均值"
            value={stats.avgValue}
            precision={2}
            valueStyle={{ color: CHART_COLORS.info }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="整体转化率"
            value={stats.overallConversion}
            precision={1}
            suffix="%"
            prefix={<PercentageOutlined />}
            valueStyle={{ color: stats.overallConversion >= 50 ? CHART_COLORS.success : CHART_COLORS.warning }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="流失总量"
            value={stats.maxValue - stats.minValue}
            valueStyle={{ color: CHART_COLORS.error }}
          />
        </Col>
      </Row>
      
      {conversionRates.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h4>转化率详情:</h4>
          <Row gutter={8}>
            {conversionRates.map((rate, index) => (
              <Col span={6} key={index}>
                <div style={{ 
                  padding: 8, 
                  backgroundColor: '#f5f5f5', 
                  borderRadius: 4,
                  textAlign: 'center'
                }}>
                  <div style={{ fontSize: 12, color: '#666' }}>
                    {rate.from} → {rate.to}
                  </div>
                  <div style={{ 
                    fontSize: 16, 
                    fontWeight: 'bold',
                    color: rate.rate >= 70 ? CHART_COLORS.success : 
                           rate.rate >= 50 ? CHART_COLORS.warning : CHART_COLORS.error
                  }}>
                    {rate.rate}%
                  </div>
                  <div style={{ fontSize: 10, color: '#999' }}>
                    流失: {rate.loss}
                  </div>
                </div>
              </Col>
            ))}
          </Row>
        </div>
      )}
      
      <ReactECharts
        option={getOption()}
        style={{ height: height, width: '100%' }}
        notMerge={true}
        lazyUpdate={true}
      />
    </Card>
  );
};

export default FunnelChart;
export type { FunnelDataItem, FunnelChartProps };