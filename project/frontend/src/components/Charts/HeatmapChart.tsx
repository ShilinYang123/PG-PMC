import React from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Select, DatePicker, Space } from 'antd';
import { CHART_COLORS } from './types';
import dayjs from 'dayjs';

interface HeatmapDataItem {
  date: string;
  hour: number;
  value: number;
  label?: string;
}

interface HeatmapChartProps {
  data: HeatmapDataItem[];
  title?: string;
  height?: number;
  showControls?: boolean;
  valueUnit?: string;
  onDateRangeChange?: (startDate: string, endDate: string) => void;
  onMetricChange?: (metric: string) => void;
}

const HeatmapChart: React.FC<HeatmapChartProps> = ({ 
  data, 
  title = '热力图分析',
  height = 400,
  showControls = true,
  valueUnit = '',
  onDateRangeChange,
  onMetricChange
}) => {
  const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, '0') + ':00');
  const dates = Array.from(new Set(data.map(item => item.date))).sort();

  const getOption = () => {
    // 转换数据格式为 ECharts 需要的格式
    const heatmapData = data.map(item => {
      const dateIndex = dates.indexOf(item.date);
      return [dateIndex, item.hour, item.value];
    });

    // 计算数值范围
    const values = data.map(item => item.value);
    const minValue = Math.min(...values);
    const maxValue = Math.max(...values);

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
        position: 'top',
        formatter: (params: any) => {
          const [dateIndex, hour, value] = params.data;
          const date = dates[dateIndex];
          const hourStr = hours[hour];
          const item = data.find(d => d.date === date && d.hour === hour);
          return `
            <div>
              <strong>日期: ${date}</strong><br/>
              时间: ${hourStr}<br/>
              数值: ${value}${valueUnit}<br/>
              ${item?.label ? `说明: ${item.label}` : ''}
            </div>
          `;
        }
      },
      grid: {
        height: '70%',
        top: '10%',
        left: '10%',
        right: '10%'
      },
      xAxis: {
        type: 'category',
        data: dates,
        splitArea: {
          show: true
        },
        axisLabel: {
          rotate: 45,
          formatter: (value: string) => {
            return dayjs(value).format('MM-DD');
          }
        }
      },
      yAxis: {
        type: 'category',
        data: hours,
        splitArea: {
          show: true
        }
      },
      visualMap: {
        min: minValue,
        max: maxValue,
        calculable: true,
        orient: 'horizontal',
        left: 'center',
        bottom: '5%',
        inRange: {
          color: ['#313695', '#4575b4', '#74add1', '#abd9e9', '#e0f3f8', '#ffffbf', '#fee090', '#fdae61', '#f46d43', '#d73027', '#a50026']
        },
        text: ['高', '低'],
        textStyle: {
          color: '#666'
        }
      },
      series: [
        {
          name: title,
          type: 'heatmap',
          data: heatmapData,
          label: {
            show: false
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    };
  };

  const getStatistics = () => {
    if (data.length === 0) return { avg: 0, max: 0, min: 0, total: 0 };
    
    const values = data.map(item => item.value);
    const total = values.reduce((sum, val) => sum + val, 0);
    const avg = total / values.length;
    const max = Math.max(...values);
    const min = Math.min(...values);
    
    return { avg: avg.toFixed(2), max, min, total: total.toFixed(2) };
  };

  const getPeakHours = () => {
    const hourStats = data.reduce((acc, item) => {
      acc[item.hour] = (acc[item.hour] || 0) + item.value;
      return acc;
    }, {} as Record<number, number>);

    const sortedHours = Object.entries(hourStats)
      .sort(([,a], [,b]) => b - a)
      .slice(0, 3)
      .map(([hour, value]) => ({ hour: parseInt(hour), value }));

    return sortedHours;
  };

  const stats = getStatistics();
  const peakHours = getPeakHours();

  return (
    <div>
      {showControls && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space>
            <span>时间范围:</span>
            <DatePicker.RangePicker
              onChange={(dates) => {
                if (dates && onDateRangeChange) {
                  onDateRangeChange(
                    dates[0]?.format('YYYY-MM-DD') || '',
                    dates[1]?.format('YYYY-MM-DD') || ''
                  );
                }
              }}
            />
            <span>指标:</span>
            <Select
              defaultValue="production"
              style={{ width: 120 }}
              onChange={onMetricChange}
              options={[
                { value: 'production', label: '生产量' },
                { value: 'efficiency', label: '效率' },
                { value: 'quality', label: '质量' },
                { value: 'energy', label: '能耗' }
              ]}
            />
          </Space>
        </Card>
      )}

      <Card>
        <div style={{ marginBottom: 16, padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>平均值</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: CHART_COLORS.primary }}>
                {stats.avg}{valueUnit}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>最大值</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: CHART_COLORS.error }}>
                {stats.max}{valueUnit}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>最小值</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold', color: CHART_COLORS.success }}>
                {stats.min}{valueUnit}
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#666' }}>峰值时段</div>
              <div style={{ fontSize: '14px', fontWeight: 'bold', color: CHART_COLORS.warning }}>
                {peakHours.map(h => hours[h.hour]).join(', ')}
              </div>
            </div>
          </div>
        </div>
        
        <ReactECharts
          option={getOption()}
          style={{ height: `${height}px` }}
          notMerge={true}
          lazyUpdate={true}
        />
      </Card>
    </div>
  );
};

export default HeatmapChart;