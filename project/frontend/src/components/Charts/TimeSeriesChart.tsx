import React, { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Select, DatePicker, Space, Button, Statistic, Row, Col } from 'antd';
import { CalendarOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';
import { CHART_COLORS } from './types';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface TimeSeriesDataPoint {
  timestamp: string | number;
  value: number;
  category?: string;
  label?: string;
}

interface TimeSeriesChartProps {
  data: TimeSeriesDataPoint[];
  title?: string;
  height?: number;
  showControls?: boolean;
  aggregationType?: 'sum' | 'avg' | 'max' | 'min' | 'count';
  timeGranularity?: 'hour' | 'day' | 'week' | 'month' | 'year';
  showTrend?: boolean;
  showForecast?: boolean;
  forecastPeriods?: number;
}

const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  data,
  title = '时间序列分析',
  height = 400,
  showControls = true,
  aggregationType = 'sum',
  timeGranularity = 'day',
  showTrend = true,
  showForecast = false,
  forecastPeriods = 7
}) => {
  const [filteredData, setFilteredData] = useState(data);
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [currentAggregation, setCurrentAggregation] = useState(aggregationType);
  const [currentGranularity, setCurrentGranularity] = useState(timeGranularity);

  // 数据聚合函数
  const aggregateData = (rawData: TimeSeriesDataPoint[], granularity: string, aggregation: string) => {
    const grouped = new Map<string, number[]>();
    
    rawData.forEach(item => {
      const date = dayjs(item.timestamp);
      let key: string;
      
      switch (granularity) {
        case 'hour':
          key = date.format('YYYY-MM-DD HH:00');
          break;
        case 'day':
          key = date.format('YYYY-MM-DD');
          break;
        case 'week':
          key = date.startOf('week').format('YYYY-MM-DD');
          break;
        case 'month':
          key = date.format('YYYY-MM');
          break;
        case 'year':
          key = date.format('YYYY');
          break;
        default:
          key = date.format('YYYY-MM-DD');
      }
      
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)!.push(item.value);
    });
    
    return Array.from(grouped.entries()).map(([key, values]) => {
      let aggregatedValue: number;
      
      switch (aggregation) {
        case 'sum':
          aggregatedValue = values.reduce((sum, val) => sum + val, 0);
          break;
        case 'avg':
          aggregatedValue = values.reduce((sum, val) => sum + val, 0) / values.length;
          break;
        case 'max':
          aggregatedValue = Math.max(...values);
          break;
        case 'min':
          aggregatedValue = Math.min(...values);
          break;
        case 'count':
          aggregatedValue = values.length;
          break;
        default:
          aggregatedValue = values.reduce((sum, val) => sum + val, 0);
      }
      
      return {
        timestamp: key,
        value: parseFloat(aggregatedValue.toFixed(2))
      };
    }).sort((a, b) => dayjs(a.timestamp).valueOf() - dayjs(b.timestamp).valueOf());
  };

  // 简单线性回归预测
  const generateForecast = (historicalData: TimeSeriesDataPoint[], periods: number) => {
    if (historicalData.length < 2) return [];
    
    const n = historicalData.length;
    const xValues = historicalData.map((_, index) => index);
    const yValues = historicalData.map(item => item.value);
    
    // 计算线性回归系数
    const sumX = xValues.reduce((sum, x) => sum + x, 0);
    const sumY = yValues.reduce((sum, y) => sum + y, 0);
    const sumXY = xValues.reduce((sum, x, i) => sum + x * yValues[i], 0);
    const sumXX = xValues.reduce((sum, x) => sum + x * x, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    // 生成预测数据
    const lastTimestamp = dayjs(historicalData[historicalData.length - 1].timestamp);
    const forecastData = [];
    
    for (let i = 1; i <= periods; i++) {
      const futureTimestamp = lastTimestamp.add(i, currentGranularity as any).format('YYYY-MM-DD');
      const predictedValue = slope * (n + i - 1) + intercept;
      
      forecastData.push({
        timestamp: futureTimestamp,
        value: Math.max(0, parseFloat(predictedValue.toFixed(2)))
      });
    }
    
    return forecastData;
  };

  // 计算统计指标
  const calculateStats = (data: TimeSeriesDataPoint[]) => {
    if (data.length === 0) return { total: 0, avg: 0, trend: 0, growth: 0 };
    
    const values = data.map(item => item.value);
    const total = values.reduce((sum, val) => sum + val, 0);
    const avg = total / values.length;
    
    // 计算趋势（最后一个值与第一个值的比较）
    const firstValue = values[0];
    const lastValue = values[values.length - 1];
    const trend = lastValue - firstValue;
    const growth = firstValue !== 0 ? ((lastValue - firstValue) / firstValue) * 100 : 0;
    
    return {
      total: parseFloat(total.toFixed(2)),
      avg: parseFloat(avg.toFixed(2)),
      trend: parseFloat(trend.toFixed(2)),
      growth: parseFloat(growth.toFixed(2))
    };
  };

  useEffect(() => {
    let processedData = data;
    
    // 日期范围过滤
    if (dateRange) {
      const [start, end] = dateRange;
      processedData = data.filter(item => {
        const itemDate = dayjs(item.timestamp);
        return itemDate.isAfter(start.startOf('day')) && itemDate.isBefore(end.endOf('day'));
      });
    }
    
    // 数据聚合
    const aggregatedData = aggregateData(processedData, currentGranularity, currentAggregation);
    setFilteredData(aggregatedData);
  }, [data, dateRange, currentAggregation, currentGranularity]);

  const stats = calculateStats(filteredData);
  const forecastData = showForecast ? generateForecast(filteredData, forecastPeriods) : [];
  const allData = [...filteredData, ...forecastData];

  const getOption = () => {
    const series: any[] = [
      {
        name: '历史数据',
        type: 'line',
        data: filteredData.map(item => [item.timestamp, item.value]),
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: {
          color: CHART_COLORS.primary,
          width: 2
        },
        itemStyle: {
          color: CHART_COLORS.primary
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: `${CHART_COLORS.primary}30` },
              { offset: 1, color: `${CHART_COLORS.primary}05` }
            ]
          }
        }
      }
    ];

    if (showForecast && forecastData.length > 0) {
      series.push({
        name: '预测数据',
        type: 'line',
        data: forecastData.map(item => [item.timestamp, item.value]),
        smooth: true,
        symbol: 'diamond',
        symbolSize: 4,
        lineStyle: {
          color: CHART_COLORS.warning,
          width: 2,
          type: 'dashed'
        },
        itemStyle: {
          color: CHART_COLORS.warning
        }
      });
    }

    if (showTrend && filteredData.length > 1) {
      // 添加趋势线
      const firstPoint = filteredData[0];
      const lastPoint = filteredData[filteredData.length - 1];
      
      series.push({
        name: '趋势线',
        type: 'line',
        data: [
          [firstPoint.timestamp, firstPoint.value],
          [lastPoint.timestamp, lastPoint.value]
        ],
        lineStyle: {
          color: CHART_COLORS.error,
          width: 1,
          type: 'solid',
          opacity: 0.6
        },
        symbol: 'none',
        silent: true
      });
    }

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
        axisPointer: {
          type: 'cross',
          label: {
            backgroundColor: '#6a7985'
          }
        },
        formatter: (params: any) => {
          let result = `${params[0].axisValue}<br/>`;
          params.forEach((param: any) => {
            result += `${param.marker}${param.seriesName}: ${param.value[1]}<br/>`;
          });
          return result;
        }
      },
      legend: {
        data: series.map(s => s.name),
        top: 30
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        top: '15%',
        containLabel: true
      },
      xAxis: {
        type: 'time',
        boundaryGap: false,
        axisLine: {
          lineStyle: {
            color: '#ccc'
          }
        }
      },
      yAxis: {
        type: 'value',
        axisLine: {
          lineStyle: {
            color: '#ccc'
          }
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0'
          }
        }
      },
      series: series,
      dataZoom: [
        {
          type: 'inside',
          start: 0,
          end: 100
        },
        {
          start: 0,
          end: 100,
          height: 30
        }
      ]
    };
  };

  return (
    <Card title={title} style={{ height: height + 200 }}>
      {showControls && (
        <Space style={{ marginBottom: 16, width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <RangePicker
              value={dateRange}
              onChange={(dates) => setDateRange(dates as [dayjs.Dayjs, dayjs.Dayjs])}
              placeholder={['开始日期', '结束日期']}
            />
            <Select
              value={currentGranularity}
              onChange={setCurrentGranularity}
              style={{ width: 100 }}
            >
              <Option value="hour">小时</Option>
              <Option value="day">天</Option>
              <Option value="week">周</Option>
              <Option value="month">月</Option>
              <Option value="year">年</Option>
            </Select>
            <Select
              value={currentAggregation}
              onChange={setCurrentAggregation}
              style={{ width: 100 }}
            >
              <Option value="sum">求和</Option>
              <Option value="avg">平均</Option>
              <Option value="max">最大</Option>
              <Option value="min">最小</Option>
              <Option value="count">计数</Option>
            </Select>
          </Space>
          <Button
            icon={<CalendarOutlined />}
            onClick={() => {
              setDateRange(null);
              setCurrentGranularity('day');
              setCurrentAggregation('sum');
            }}
          >
            重置
          </Button>
        </Space>
      )}
      
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Statistic
            title="总计"
            value={stats.total}
            precision={2}
            valueStyle={{ color: CHART_COLORS.primary }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="平均值"
            value={stats.avg}
            precision={2}
            valueStyle={{ color: CHART_COLORS.info }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="趋势"
            value={stats.trend > 0 ? '上升' : '下降'}
            prefix={stats.trend > 0 ? <RiseOutlined style={{ color: '#52c41a' }} /> : <FallOutlined style={{ color: '#ff4d4f' }} />}
            valueStyle={{ color: stats.trend > 0 ? '#52c41a' : '#ff4d4f' }}
          />
        </Col>
        <Col span={6}>
          <Statistic
            title="增长率"
            value={stats.growth}
            precision={2}
            suffix="%"
            prefix={stats.growth >= 0 ? <RiseOutlined /> : <FallOutlined />}
            valueStyle={{ color: stats.growth >= 0 ? CHART_COLORS.success : CHART_COLORS.error }}
          />
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

export default TimeSeriesChart;
export type { TimeSeriesDataPoint, TimeSeriesChartProps };