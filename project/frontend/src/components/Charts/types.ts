// 图表组件数据类型定义

// 生产进度图表数据
export interface ProductionProgressData {
  orderId: string;
  orderName: string;
  totalQuantity: number;
  completedQuantity: number;
  plannedQuantity: number;
  progress: number;
  status: 'pending' | 'in_progress' | 'completed' | 'delayed';
  startDate: string;
  endDate: string;
}

// 订单状态图表数据
export interface OrderStatusData {
  status: string;
  count: number;
  percentage: number;
  color: string;
}

// 设备状态图表数据
export interface EquipmentStatusData {
  equipmentId: string;
  equipmentName: string;
  status: 'running' | 'idle' | 'maintenance' | 'error';
  utilization: number;
  lastMaintenance: string;
  nextMaintenance: string;
}

// 质量趋势图表数据
export interface QualityTrendData {
  date: string;
  passRate: number;
  defectRate: number;
  reworkRate: number;
  totalInspected: number;
}

// 物料库存图表数据
export interface MaterialInventoryData {
  materialId: string;
  materialName: string;
  currentStock: number;
  minStock: number;
  maxStock: number;
  unit: string;
  status: 'normal' | 'low' | 'critical' | 'overstock';
}

// 通用图表配置
export interface ChartConfig {
  title?: string;
  height?: number;
  showLegend?: boolean;
  showTooltip?: boolean;
}

// 仪表盘图表数据类型
export interface DashboardData {
  title: string;
  value: number;
  max: number;
  unit: string;
  status: 'normal' | 'warning' | 'critical';
  trend?: number;
}

// 雷达图数据类型
export interface RadarDataItem {
  name: string;
  values: number[];
  color?: string;
}

export interface RadarIndicator {
  name: string;
  max: number;
  unit?: string;
}

// 热力图数据类型
export interface HeatmapDataItem {
  date: string;
  hour: number;
  value: number;
  label?: string;
}

// 多轴图表数据类型
export interface SeriesData {
  name: string;
  data: number[];
  type: 'line' | 'bar';
  yAxisIndex: number;
  color?: string;
  unit?: string;
  smooth?: boolean;
  stack?: string;
}

export interface YAxisConfig {
  name: string;
  unit: string;
  position: 'left' | 'right';
  min?: number;
  max?: number;
  color?: string;
}

// 实时图表数据类型
export interface RealTimeDataPoint {
  timestamp: number;
  value: number;
  status?: 'normal' | 'warning' | 'error';
  label?: string;
}

// 图表颜色主题
export const CHART_COLORS = {
  primary: '#1890ff',
  success: '#52c41a',
  warning: '#faad14',
  error: '#ff4d4f',
  info: '#13c2c2',
  purple: '#722ed1',
  orange: '#fa8c16',
  gray: '#8c8c8c'
};

// 状态颜色映射
export const STATUS_COLORS = {
  pending: CHART_COLORS.gray,
  in_progress: CHART_COLORS.primary,
  completed: CHART_COLORS.success,
  delayed: CHART_COLORS.error,
  running: CHART_COLORS.success,
  idle: CHART_COLORS.warning,
  maintenance: CHART_COLORS.info,
  error: CHART_COLORS.error,
  normal: CHART_COLORS.success,
  low: CHART_COLORS.warning,
  critical: CHART_COLORS.error,
  overstock: CHART_COLORS.purple,
  success: CHART_COLORS.success
};

// 基础图表组件类型
export type {
  LineChartData,
  LineChartProps
} from './LineChart';

export type {
  BarChartData,
  BarChartProps
} from './BarChart';

export type {
  PieChartData,
  PieChartProps
} from './PieChart';

// 别名导出
export type {
  BarChartData as ColumnChartData,
  BarChartProps as ColumnChartProps
} from './BarChart';

export type {
  PieChartData as DonutChartData,
  PieChartProps as DonutChartProps
} from './PieChart';

// 高级图表组件类型
export type {
  Map3DDataItem,
  Map3DChartProps
} from './Map3DChart';

export type {
  TimeSeriesDataPoint,
  TimeSeriesChartProps
} from './TimeSeriesChart';

export type {
  Bar3DDataItem,
  Bar3DChartProps
} from './Bar3DChart';

export type {
  NetworkNode,
  NetworkLink,
  NetworkCategory,
  NetworkChartProps
} from './NetworkChart';

export type {
  SankeyNode,
  SankeyLink,
  SankeyChartProps
} from './SankeyChart';

export type {
  FunnelDataItem,
  FunnelChartProps
} from './FunnelChart';

// 业务图表组件类型已在上方定义，无需重复导出