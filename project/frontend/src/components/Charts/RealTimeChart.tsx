import React, { useEffect, useRef, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Button, Space, Statistic, Tag, Switch } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined, ReloadOutlined } from '@ant-design/icons';
import { CHART_COLORS } from './types';

interface RealTimeDataPoint {
  timestamp: number;
  value: number;
  status?: 'normal' | 'warning' | 'error';
  label?: string;
}

interface RealTimeChartProps {
  title?: string;
  height?: number;
  maxDataPoints?: number;
  updateInterval?: number;
  dataSource?: () => Promise<RealTimeDataPoint>;
  initialData?: RealTimeDataPoint[];
  unit?: string;
  thresholds?: {
    warning: number;
    error: number;
  };
  showControls?: boolean;
}

const RealTimeChart: React.FC<RealTimeChartProps> = ({ 
  title = '实时数据监控',
  height = 400,
  maxDataPoints = 50,
  updateInterval = 2000,
  dataSource,
  initialData = [],
  unit = '',
  thresholds,
  showControls = true
}) => {
  const [data, setData] = useState<RealTimeDataPoint[]>(initialData);
  const [isRunning, setIsRunning] = useState(false);
  const [autoScale, setAutoScale] = useState(true);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const chartRef = useRef<any>(null);

  // 模拟数据生成器
  const generateMockData = (): RealTimeDataPoint => {
    const now = Date.now();
    const baseValue = 50;
    const variation = (Math.random() - 0.5) * 20;
    const value = Math.max(0, baseValue + variation);
    
    let status: 'normal' | 'warning' | 'error' = 'normal';
    if (thresholds) {
      if (value >= thresholds.error) status = 'error';
      else if (value >= thresholds.warning) status = 'warning';
    }
    
    return {
      timestamp: now,
      value: parseFloat(value.toFixed(2)),
      status
    };
  };

  const addDataPoint = async () => {
    try {
      const newPoint = dataSource ? await dataSource() : generateMockData();
      
      setData(prevData => {
        const newData = [...prevData, newPoint];
        // 保持最大数据点数量
        if (newData.length > maxDataPoints) {
          return newData.slice(-maxDataPoints);
        }
        return newData;
      });
    } catch (error) {
      console.error('获取实时数据失败:', error);
    }
  };

  const startMonitoring = () => {
    if (intervalRef.current) return;
    
    setIsRunning(true);
    intervalRef.current = setInterval(addDataPoint, updateInterval);
  };

  const stopMonitoring = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsRunning(false);
  };

  const clearData = () => {
    setData([]);
  };

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const getOption = () => {
    const xAxisData = data.map(point => new Date(point.timestamp).toLocaleTimeString());
    const seriesData = data.map(point => ({
      value: point.value,
      itemStyle: {
        color: point.status === 'error' ? CHART_COLORS.error :
               point.status === 'warning' ? CHART_COLORS.warning :
               CHART_COLORS.success
      }
    }));

    const values = data.map(point => point.value);
    const minValue = values.length > 0 ? Math.min(...values) : 0;
    const maxValue = values.length > 0 ? Math.max(...values) : 100;
    const padding = (maxValue - minValue) * 0.1;

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
        trigger: 'axis',
        formatter: (params: any) => {
          const dataIndex = params[0].dataIndex;
          const point = data[dataIndex];
          return `
            <div>
              <strong>时间: ${new Date(point.timestamp).toLocaleString()}</strong><br/>
              数值: ${point.value}${unit}<br/>
              状态: ${point.status === 'error' ? '异常' : point.status === 'warning' ? '警告' : '正常'}<br/>
              ${point.label ? `说明: ${point.label}` : ''}
            </div>
          `;
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: xAxisData,
        boundaryGap: false,
        axisLabel: {
          rotate: 45
        }
      },
      yAxis: {
        type: 'value',
        min: autoScale ? undefined : minValue - padding,
        max: autoScale ? undefined : maxValue + padding,
        axisLabel: {
          formatter: `{value}${unit}`
        }
      },
      series: [
        {
          name: '实时数据',
          type: 'line',
          data: seriesData,
          smooth: true,
          symbol: 'circle',
          symbolSize: 4,
          lineStyle: {
            width: 2
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0,
              y: 0,
              x2: 0,
              y2: 1,
              colorStops: [
                {
                  offset: 0,
                  color: CHART_COLORS.primary + '40'
                },
                {
                  offset: 1,
                  color: CHART_COLORS.primary + '10'
                }
              ]
            }
          },
          markLine: thresholds ? {
            data: [
              {
                yAxis: thresholds.warning,
                lineStyle: {
                  color: CHART_COLORS.warning,
                  type: 'dashed'
                },
                label: {
                  formatter: `警告线: ${thresholds.warning}${unit}`
                }
              },
              {
                yAxis: thresholds.error,
                lineStyle: {
                  color: CHART_COLORS.error,
                  type: 'dashed'
                },
                label: {
                  formatter: `错误线: ${thresholds.error}${unit}`
                }
              }
            ]
          } : undefined
        }
      ]
    };
  };

  const getLatestValue = () => {
    return data.length > 0 ? data[data.length - 1] : null;
  };

  const getStatistics = () => {
    if (data.length === 0) return { avg: 0, max: 0, min: 0, trend: 0 };
    
    const values = data.map(point => point.value);
    const sum = values.reduce((acc, val) => acc + val, 0);
    const avg = sum / values.length;
    const max = Math.max(...values);
    const min = Math.min(...values);
    
    // 计算趋势（最近5个点的斜率）
    let trend = 0;
    if (data.length >= 5) {
      const recent = data.slice(-5);
      const firstValue = recent[0].value;
      const lastValue = recent[recent.length - 1].value;
      trend = ((lastValue - firstValue) / firstValue) * 100;
    }
    
    return {
      avg: avg.toFixed(2),
      max,
      min,
      trend: trend.toFixed(1)
    };
  };

  const latest = getLatestValue();
  const stats = getStatistics();

  return (
    <div>
      {showControls && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space wrap>
            <Button
              type={isRunning ? 'default' : 'primary'}
              icon={isRunning ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={isRunning ? stopMonitoring : startMonitoring}
            >
              {isRunning ? '暂停' : '开始'}
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={clearData}
              disabled={isRunning}
            >
              清空数据
            </Button>
            <Space>
              <span>自动缩放:</span>
              <Switch 
                checked={autoScale} 
                onChange={setAutoScale}
                size="small"
              />
            </Space>
            <Tag color={isRunning ? 'green' : 'red'}>
              {isRunning ? '监控中' : '已停止'}
            </Tag>
            <span style={{ color: '#666', fontSize: '12px' }}>
              数据点: {data.length}/{maxDataPoints}
            </span>
          </Space>
        </Card>
      )}

      <Card>
        <div style={{ marginBottom: 16, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
            <div>
              <Statistic
                title="当前值"
                value={latest?.value || 0}
                suffix={unit}
                valueStyle={{ 
                  color: latest?.status === 'error' ? '#ff4d4f' :
                         latest?.status === 'warning' ? '#faad14' : '#52c41a',
                  fontSize: '18px'
                }}
              />
            </div>
            <div>
              <Statistic
                title="平均值"
                value={stats.avg}
                suffix={unit}
                valueStyle={{ fontSize: '16px' }}
              />
            </div>
            <div>
              <Statistic
                title="最大值"
                value={stats.max}
                suffix={unit}
                valueStyle={{ color: '#ff4d4f', fontSize: '16px' }}
              />
            </div>
            <div>
              <Statistic
                title="最小值"
                value={stats.min}
                suffix={unit}
                valueStyle={{ color: '#52c41a', fontSize: '16px' }}
              />
            </div>
            <div>
              <Statistic
                title="趋势"
                value={stats.trend}
                suffix="%"
                prefix={parseFloat(stats.trend.toString()) > 0 ? '↗' : parseFloat(stats.trend.toString()) < 0 ? '↘' : '→'}
                valueStyle={{
                  color: parseFloat(stats.trend.toString()) > 0 ? '#52c41a' :
                         parseFloat(stats.trend.toString()) < 0 ? '#ff4d4f' : '#666',        
                  fontSize: '16px'
                }}
              />
            </div>
          </div>
        </div>
        
        <ReactECharts
          ref={chartRef}
          option={getOption()}
          style={{ height: `${height}px` }}
          notMerge={true}
          lazyUpdate={true}
        />
      </Card>
    </div>
  );
};

export default RealTimeChart;