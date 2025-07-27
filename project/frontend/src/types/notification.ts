// 通知类型定义
export enum NotificationType {
  ORDER_REMINDER = 'order_reminder',
  PRODUCTION_ALERT = 'production_alert',
  MATERIAL_WARNING = 'material_warning',
  EQUIPMENT_MAINTENANCE = 'equipment_maintenance',
  QUALITY_ISSUE = 'quality_issue',
  SYSTEM_NOTIFICATION = 'system_notification'
}

export enum NotificationPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent'
}

export enum NotificationStatus {
  PENDING = 'pending',
  SENT = 'sent',
  READ = 'read',
  FAILED = 'failed'
}

export interface Notification {
  id: number;
  title: string;
  content: string;
  notification_type: NotificationType;
  priority: NotificationPriority;
  status: NotificationStatus;
  recipient_id: number;
  sender_id?: number;
  template_id?: number;
  scheduled_at?: string;
  sent_at?: string;
  read_at?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface NotificationTemplate {
  id: number;
  name: string;
  title_template: string;
  content_template: string;
  notification_type: NotificationType;
  is_active: boolean;
  variables?: string[];
  created_at: string;
  updated_at: string;
}

export interface NotificationRule {
  id: number;
  name: string;
  description?: string;
  trigger_event: string;
  conditions: Record<string, any>;
  template_id: number;
  target_users?: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationStats {
  total_count: number;
  unread_count: number;
  sent_count: number;
  failed_count: number;
  by_type: Record<NotificationType, number>;
  by_priority: Record<NotificationPriority, number>;
}

export interface NotificationQuery {
  notification_type?: NotificationType;
  status?: NotificationStatus;
  priority?: NotificationPriority;
  start_date?: string;
  end_date?: string;
  page?: number;
  size?: number;
}

export interface NotificationCreate {
  title: string;
  content: string;
  notification_type: NotificationType;
  priority: NotificationPriority;
  recipient_id: number;
  template_id?: number;
  scheduled_at?: string;
  metadata?: Record<string, any>;
}

export interface NotificationUpdate {
  title?: string;
  content?: string;
  priority?: NotificationPriority;
  status?: NotificationStatus;
  scheduled_at?: string;
  metadata?: Record<string, any>;
}

export interface BatchNotificationCreate {
  title: string;
  content: string;
  notification_type: NotificationType;
  priority: NotificationPriority;
  recipient_ids: number[];
  template_id?: number;
  scheduled_at?: string;
  metadata?: Record<string, any>;
}

// 通知显示配置
export const NOTIFICATION_TYPE_LABELS: Record<NotificationType, string> = {
  [NotificationType.ORDER_REMINDER]: '订单提醒',
  [NotificationType.PRODUCTION_ALERT]: '生产警报',
  [NotificationType.MATERIAL_WARNING]: '物料预警',
  [NotificationType.EQUIPMENT_MAINTENANCE]: '设备维护',
  [NotificationType.QUALITY_ISSUE]: '质量问题',
  [NotificationType.SYSTEM_NOTIFICATION]: '系统通知'
};

export const NOTIFICATION_PRIORITY_LABELS: Record<NotificationPriority, string> = {
  [NotificationPriority.LOW]: '低',
  [NotificationPriority.MEDIUM]: '中',
  [NotificationPriority.HIGH]: '高',
  [NotificationPriority.URGENT]: '紧急'
};

export const NOTIFICATION_STATUS_LABELS: Record<NotificationStatus, string> = {
  [NotificationStatus.PENDING]: '待发送',
  [NotificationStatus.SENT]: '已发送',
  [NotificationStatus.READ]: '已读',
  [NotificationStatus.FAILED]: '发送失败'
};

// 通知颜色配置
export const NOTIFICATION_TYPE_COLORS: Record<NotificationType, string> = {
  [NotificationType.ORDER_REMINDER]: '#1890ff',
  [NotificationType.PRODUCTION_ALERT]: '#fa8c16',
  [NotificationType.MATERIAL_WARNING]: '#faad14',
  [NotificationType.EQUIPMENT_MAINTENANCE]: '#722ed1',
  [NotificationType.QUALITY_ISSUE]: '#f5222d',
  [NotificationType.SYSTEM_NOTIFICATION]: '#52c41a'
};

export const NOTIFICATION_PRIORITY_COLORS: Record<NotificationPriority, string> = {
  [NotificationPriority.LOW]: '#52c41a',
  [NotificationPriority.MEDIUM]: '#1890ff',
  [NotificationPriority.HIGH]: '#fa8c16',
  [NotificationPriority.URGENT]: '#f5222d'
};

export const NOTIFICATION_STATUS_COLORS: Record<NotificationStatus, string> = {
  [NotificationStatus.PENDING]: '#faad14',
  [NotificationStatus.SENT]: '#1890ff',
  [NotificationStatus.READ]: '#52c41a',
  [NotificationStatus.FAILED]: '#f5222d'
};