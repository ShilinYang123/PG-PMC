import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Tag,
  Space,
  Spin,
  message,
  Button,
  Tooltip
} from 'antd';
import {
  BellOutlined,
  CheckOutlined,
  SendOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  ReloadOutlined,
  RiseOutlined
} from '@ant-design/icons';
import {
  NotificationStats as INotificationStats,
  NotificationType,
  NotificationPriority,
  NOTIFICATION_TYPE_LABELS,
  NOTIFICATION_PRIORITY_LABELS,
  NOTIFICATION_TYPE_COLORS,
  NOTIFICATION_PRIORITY_COLORS
} from '../../types/notification';
import notificationService from '../../services/notificationService';

interface NotificationStatsProps {
  isAdmin?: boolean;
  refreshInterval?: number; // 自动刷新间隔（毫秒）
  onStatsChange?: (stats: INotificationStats) => void;
}

const NotificationStats: React.FC<NotificationStatsProps> = ({
  isAdmin = false,
  refreshInterval = 30000, // 默认30秒刷新
  onStatsChange
}) => {
  const [stats, setStats] = useState<INotificationStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdateTime, setLastUpdateTime] = useState<Date | null>(null);

  // 加载统计数据
  const loadStats = async () => {
    try {
      setLoading(true);
      const data = isAdmin 
        ? await notificationService.getAdminNotificationStats()
        : await notificationService.getNotificationStats();
      
      setStats(data);
      setLastUpdateTime(new Date());
      onStatsChange?.(data);
    } catch (error) {
      message.error('加载统计数据失败');
      console.error('Load stats error:', error);
    } finally {
      setLoading(false);
    }
  };

  // 初始加载和定时刷新
  useEffect(() => {
    loadStats();

    const interval = setInterval(loadStats, refreshInterval);
    return () => clearInterval(interval);
  }, [isAdmin, refreshInterval]);

  // 计算百分比
  const getPercentage = (value: number, total: number) => {
    return total > 0 ? Math.round((value / total) * 100) : 0;
  };

  // 获取状态颜色
  const getStatusColor = (type: 'unread' | 'sent' | 'failed') => {
    switch (type) {
      case 'unread':
        return '#faad14';
      case 'sent':
        return '#52c41a';
      case 'failed':
        return '#f5222d';
      default:
        return '#1890ff';
    }
  };

  if (!stats) {
    return (
      <Card>
        <Spin spinning={loading}>
          <div style={{ height: '200px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span>加载统计数据中...</span>
          </div>
        </Spin>
      </Card>
    );
  }

  return (
    <div>
      {/* 总体统计 */}
      <Card
        title={
          <Space>
            <RiseOutlined />
            <span>{isAdmin ? '系统通知统计' : '我的通知统计'}</span>
          </Space>
        }
        extra={
          <Space>
            {lastUpdateTime && (
              <Tooltip title={`最后更新: ${lastUpdateTime.toLocaleString()}`}>
                <span style={{ fontSize: '12px', color: '#666' }}>
                  {lastUpdateTime.toLocaleTimeString()}
                </span>
              </Tooltip>
            )}
            <Button
              type="text"
              icon={<ReloadOutlined />}
              loading={loading}
              onClick={loadStats}
            >
              刷新
            </Button>
          </Space>
        }
      >
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={6}>
            <Statistic
              title="总通知数"
              value={stats.total_count}
              prefix={<BellOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="未读通知"
              value={stats.unread_count}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: getStatusColor('unread') }}
              suffix={
                <span style={{ fontSize: '14px' }}>
                  ({getPercentage(stats.unread_count, stats.total_count)}%)
                </span>
              }
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="已发送"
              value={stats.sent_count}
              prefix={<SendOutlined />}
              valueStyle={{ color: getStatusColor('sent') }}
              suffix={
                <span style={{ fontSize: '14px' }}>
                  ({getPercentage(stats.sent_count, stats.total_count)}%)
                </span>
              }
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="发送失败"
              value={stats.failed_count}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: getStatusColor('failed') }}
              suffix={
                <span style={{ fontSize: '14px' }}>
                  ({getPercentage(stats.failed_count, stats.total_count)}%)
                </span>
              }
            />
          </Col>
        </Row>

        {/* 进度条显示 */}
        <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
          <Col span={12}>
            <div>
              <div style={{ marginBottom: '8px' }}>
                <span>已读率</span>
                <span style={{ float: 'right' }}>
                  {getPercentage(stats.total_count - stats.unread_count, stats.total_count)}%
                </span>
              </div>
              <Progress
                percent={getPercentage(stats.total_count - stats.unread_count, stats.total_count)}
                strokeColor={getStatusColor('sent')}
                showInfo={false}
              />
            </div>
          </Col>
          <Col span={12}>
            <div>
              <div style={{ marginBottom: '8px' }}>
                <span>发送成功率</span>
                <span style={{ float: 'right' }}>
                  {getPercentage(stats.sent_count, stats.total_count)}%
                </span>
              </div>
              <Progress
                percent={getPercentage(stats.sent_count, stats.total_count)}
                strokeColor={getStatusColor('sent')}
                showInfo={false}
              />
            </div>
          </Col>
        </Row>
      </Card>

      {/* 按类型统计 */}
      <Card
        title="按类型统计"
        style={{ marginTop: '16px' }}
        size="small"
      >
        <Row gutter={[16, 16]}>
          {Object.entries(stats.by_type).map(([type, count]) => {
            const notificationType = type as NotificationType;
            const percentage = getPercentage(count, stats.total_count);
            
            return (
              <Col xs={12} sm={8} md={6} key={type}>
                <Card size="small" style={{ textAlign: 'center' }}>
                  <Statistic
                    title={
                      <Tag color={NOTIFICATION_TYPE_COLORS[notificationType]}>
                        {NOTIFICATION_TYPE_LABELS[notificationType]}
                      </Tag>
                    }
                    value={count}
                    suffix={<span style={{ fontSize: '12px' }}>({percentage}%)</span>}
                    valueStyle={{ 
                      color: NOTIFICATION_TYPE_COLORS[notificationType],
                      fontSize: '18px'
                    }}
                  />
                  <Progress
                    percent={percentage}
                    strokeColor={NOTIFICATION_TYPE_COLORS[notificationType]}
                    showInfo={false}
                    size="small"
                    style={{ marginTop: '8px' }}
                  />
                </Card>
              </Col>
            );
          })}
        </Row>
      </Card>

      {/* 按优先级统计 */}
      <Card
        title="按优先级统计"
        style={{ marginTop: '16px' }}
        size="small"
      >
        <Row gutter={[16, 16]}>
          {Object.entries(stats.by_priority).map(([priority, count]) => {
            const notificationPriority = priority as NotificationPriority;
            const percentage = getPercentage(count, stats.total_count);
            
            return (
              <Col xs={12} sm={6} key={priority}>
                <Card size="small" style={{ textAlign: 'center' }}>
                  <Statistic
                    title={
                      <Tag color={NOTIFICATION_PRIORITY_COLORS[notificationPriority]}>
                        {NOTIFICATION_PRIORITY_LABELS[notificationPriority]}
                      </Tag>
                    }
                    value={count}
                    suffix={<span style={{ fontSize: '12px' }}>({percentage}%)</span>}
                    valueStyle={{ 
                      color: NOTIFICATION_PRIORITY_COLORS[notificationPriority],
                      fontSize: '18px'
                    }}
                  />
                  <Progress
                    percent={percentage}
                    strokeColor={NOTIFICATION_PRIORITY_COLORS[notificationPriority]}
                    showInfo={false}
                    size="small"
                    style={{ marginTop: '8px' }}
                  />
                </Card>
              </Col>
            );
          })}
        </Row>
      </Card>

      {/* 快速操作提示 */}
      {stats.unread_count > 0 && (
        <Card
          style={{ marginTop: '16px', backgroundColor: '#fff7e6', border: '1px solid #ffd591' }}
          size="small"
        >
          <Space>
            <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />
            <span>您有 {stats.unread_count} 条未读通知</span>
            {stats.failed_count > 0 && (
              <span style={{ color: '#f5222d' }}>，{stats.failed_count} 条发送失败</span>
            )}
          </Space>
        </Card>
      )}
    </div>
  );
};

export default NotificationStats;