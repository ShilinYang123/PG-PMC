import React, { useState, useEffect } from 'react';
import {
  Modal,
  Card,
  Descriptions,
  Tag,
  Button,
  Space,
  Typography,
  Divider,
  message,
  Spin,
  Alert,
  Timeline,
  Badge
} from 'antd';
import {
  BellOutlined,
  CheckOutlined,
  DeleteOutlined,
  SendOutlined,
  ClockCircleOutlined,
  UserOutlined,
  FileTextOutlined
} from '@ant-design/icons';
// import { formatDistanceToNow, format } from 'date-fns';
// import { zhCN } from 'date-fns/locale';
import {
  Notification,
  NotificationType,
  NotificationPriority,
  NotificationStatus,
  NOTIFICATION_TYPE_LABELS,
  NOTIFICATION_PRIORITY_LABELS,
  NOTIFICATION_STATUS_LABELS,
  NOTIFICATION_TYPE_COLORS,
  NOTIFICATION_PRIORITY_COLORS,
  NOTIFICATION_STATUS_COLORS
} from '../../types/notification';
import notificationService from '../../services/notificationService';

const { Title, Text, Paragraph } = Typography;

interface NotificationDetailProps {
  notificationId?: number;
  notification?: Notification;
  visible: boolean;
  onClose: () => void;
  onUpdate?: () => void;
  showActions?: boolean;
}

const NotificationDetail: React.FC<NotificationDetailProps> = ({
  notificationId,
  notification: propNotification,
  visible,
  onClose,
  onUpdate,
  showActions = true
}) => {
  const [notification, setNotification] = useState<Notification | null>(propNotification || null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  // 加载通知详情
  const loadNotification = async () => {
    if (!notificationId || propNotification) return;

    try {
      setLoading(true);
      const data = await notificationService.getNotification(notificationId);
      setNotification(data);
    } catch (error) {
      message.error('加载通知详情失败');
      console.error('Load notification error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible) {
      if (propNotification) {
        setNotification(propNotification);
      } else {
        loadNotification();
      }
    }
  }, [visible, notificationId, propNotification]);

  // 标记为已读
  const handleMarkAsRead = async () => {
    if (!notification) return;

    try {
      setActionLoading('read');
      await notificationService.markAsRead(notification.id);
      message.success('已标记为已读');
      
      // 更新本地状态
      setNotification(prev => prev ? {
        ...prev,
        status: NotificationStatus.READ,
        read_at: new Date().toISOString()
      } : null);
      
      onUpdate?.();
    } catch (error) {
      message.error('标记失败');
    } finally {
      setActionLoading(null);
    }
  };

  // 删除通知
  const handleDelete = async () => {
    if (!notification) return;

    try {
      setActionLoading('delete');
      await notificationService.deleteNotification(notification.id);
      message.success('删除成功');
      onUpdate?.();
      onClose();
    } catch (error) {
      message.error('删除失败');
    } finally {
      setActionLoading(null);
    }
  };

  // 重新发送通知
  const handleResend = async () => {
    if (!notification) return;

    try {
      setActionLoading('send');
      await notificationService.sendNotification(notification.id);
      message.success('重新发送成功');
      onUpdate?.();
    } catch (error) {
      message.error('发送失败');
    } finally {
      setActionLoading(null);
    }
  };

  // 获取状态图标
  const getStatusIcon = (status: NotificationStatus) => {
    switch (status) {
      case NotificationStatus.PENDING:
        return <ClockCircleOutlined style={{ color: NOTIFICATION_STATUS_COLORS[status] }} />;
      case NotificationStatus.SENT:
        return <SendOutlined style={{ color: NOTIFICATION_STATUS_COLORS[status] }} />;
      case NotificationStatus.READ:
        return <CheckOutlined style={{ color: NOTIFICATION_STATUS_COLORS[status] }} />;
      case NotificationStatus.FAILED:
        return <DeleteOutlined style={{ color: NOTIFICATION_STATUS_COLORS[status] }} />;
      default:
        return <BellOutlined />;
    }
  };

  // 渲染时间线
  const renderTimeline = () => {
    if (!notification) return null;

    const timelineItems = [
      {
        dot: <BellOutlined style={{ color: '#1890ff' }} />,
        children: (
          <div>
            <Text strong>通知创建</Text>
            <br />
            <Text type="secondary">
              {new Date(notification.created_at).toLocaleString()}
            </Text>
          </div>
        )
      }
    ];

    if (notification.scheduled_at) {
      timelineItems.push({
        dot: <ClockCircleOutlined style={{ color: '#faad14' }} />,
        children: (
          <div>
            <Text strong>计划发送时间</Text>
            <br />
            <Text type="secondary">
              {new Date(notification.scheduled_at).toLocaleString()}
            </Text>
          </div>
        )
      });
    }

    if (notification.sent_at) {
      timelineItems.push({
        dot: <SendOutlined style={{ color: '#52c41a' }} />,
        children: (
          <div>
            <Text strong>发送成功</Text>
            <br />
            <Text type="secondary">
              {new Date(notification.sent_at).toLocaleString()}
            </Text>
          </div>
        )
      });
    }

    if (notification.read_at) {
      timelineItems.push({
        dot: <CheckOutlined style={{ color: '#52c41a' }} />,
        children: (
          <div>
            <Text strong>已读</Text>
            <br />
            <Text type="secondary">
              {new Date(notification.read_at).toLocaleString()}
            </Text>
          </div>
        )
      });
    }

    return <Timeline items={timelineItems} />;
  };

  // 渲染元数据
  const renderMetadata = () => {
    if (!notification?.metadata || Object.keys(notification.metadata).length === 0) {
      return null;
    }

    return (
      <Card size="small" title="附加信息" style={{ marginTop: '16px' }}>
        <Descriptions column={1} size="small">
          {Object.entries(notification.metadata).map(([key, value]) => (
            <Descriptions.Item key={key} label={key}>
              {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
            </Descriptions.Item>
          ))}
        </Descriptions>
      </Card>
    );
  };

  if (!notification && !loading) {
    return (
      <Modal
        title="通知详情"
        open={visible}
        onCancel={onClose}
        footer={null}
        width={800}
      >
        <Alert message="通知不存在或已被删除" type="warning" />
      </Modal>
    );
  }

  return (
    <Modal
      title={
        <Space>
          <BellOutlined />
          <span>通知详情</span>
          {notification && notification.status !== NotificationStatus.READ && (
            <Badge dot />
          )}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width={800}
      footer={
        showActions && notification ? (
          <Space>
            {notification.status !== NotificationStatus.READ && (
              <Button
                type="primary"
                icon={<CheckOutlined />}
                loading={actionLoading === 'read'}
                onClick={handleMarkAsRead}
              >
                标记为已读
              </Button>
            )}
            {notification.status === NotificationStatus.FAILED && (
              <Button
                icon={<SendOutlined />}
                loading={actionLoading === 'send'}
                onClick={handleResend}
              >
                重新发送
              </Button>
            )}
            <Button
              danger
              icon={<DeleteOutlined />}
              loading={actionLoading === 'delete'}
              onClick={handleDelete}
            >
              删除
            </Button>
            <Button onClick={onClose}>关闭</Button>
          </Space>
        ) : (
          <Button onClick={onClose}>关闭</Button>
        )
      }
    >
      <Spin spinning={loading}>
        {notification && (
          <div>
            {/* 基本信息 */}
            <Card size="small" title="基本信息">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="标题" span={2}>
                  <Title level={4} style={{ margin: 0 }}>
                    {notification.title}
                  </Title>
                </Descriptions.Item>
                <Descriptions.Item label="类型">
                  <Tag 
                    color={NOTIFICATION_TYPE_COLORS[notification.notification_type]}
                    icon={<BellOutlined />}
                  >
                    {NOTIFICATION_TYPE_LABELS[notification.notification_type]}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="优先级">
                  <Tag color={NOTIFICATION_PRIORITY_COLORS[notification.priority]}>
                    {NOTIFICATION_PRIORITY_LABELS[notification.priority]}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="状态">
                  <Tag 
                    color={NOTIFICATION_STATUS_COLORS[notification.status]}
                    icon={getStatusIcon(notification.status)}
                  >
                    {NOTIFICATION_STATUS_LABELS[notification.status]}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="创建时间">
                  <Space direction="vertical" size={0}>
                    <Text>{new Date(notification.created_at).toLocaleString()}</Text>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      {Math.floor((Date.now() - new Date(notification.created_at).getTime()) / (1000 * 60 * 60 * 24))} 天前
                    </Text>
                  </Space>
                </Descriptions.Item>
                {notification.recipient_id && (
                  <Descriptions.Item label="接收人ID">
                    <Tag icon={<UserOutlined />}>
                      {notification.recipient_id}
                    </Tag>
                  </Descriptions.Item>
                )}
                {notification.sender_id && (
                  <Descriptions.Item label="发送人ID">
                    <Tag icon={<UserOutlined />}>
                      {notification.sender_id}
                    </Tag>
                  </Descriptions.Item>
                )}
                {notification.template_id && (
                  <Descriptions.Item label="模板ID">
                    <Tag icon={<FileTextOutlined />}>
                      {notification.template_id}
                    </Tag>
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>

            <Divider />

            {/* 通知内容 */}
            <Card size="small" title="通知内容">
              <Paragraph style={{ whiteSpace: 'pre-wrap' }}>
                {notification.content}
              </Paragraph>
            </Card>

            <Divider />

            {/* 时间线 */}
            <Card size="small" title="处理时间线">
              {renderTimeline()}
            </Card>

            {/* 元数据 */}
            {renderMetadata()}
          </div>
        )}
      </Spin>
    </Modal>
  );
};

export default NotificationDetail;