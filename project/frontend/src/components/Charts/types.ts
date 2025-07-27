// 图表组件数据类型定义

// 生产进度图表数据
export interface ProductionProgressData {
  orderId: string;
  orderName: string;
  totalQuantity: number;
  completedQuantity: number;
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
  width?: number;
  showLegend?: boolean;
  showTooltip?: boolean;
  theme?: 'light' | 'dark';
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