import React, { useState, useEffect } from 'react';
import {
  List,
  Card,
  Badge,
  Tag,
  Button,
  Space,
  Typography,
  Tooltip,
  Checkbox,
  message,
  Popconfirm,
  Empty,
  Spin,
  Select,
  DatePicker,
  Input,
  Row,
  Col
} from 'antd';
import {
  BellOutlined,
  DeleteOutlined,
  EyeOutlined,
  CheckOutlined,
  ReloadOutlined,
  ExportOutlined,
  FilterOutlined
} from '@ant-design/icons';
// date-fns imports removed due to module issues
import {
  Notification,
  NotificationType,
  NotificationPriority,
  NotificationStatus,
  NotificationQuery,
  NOTIFICATION_TYPE_LABELS,
  NOTIFICATION_PRIORITY_LABELS,
  NOTIFICATION_STATUS_LABELS,
  NOTIFICATION_TYPE_COLORS,
  NOTIFICATION_PRIORITY_COLORS,
  NOTIFICATION_STATUS_COLORS
} from '../../types/notification';
import notificationService from '../../services/notificationService';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { Search } = Input;

interface NotificationListProps {
  height?: number;
  showFilters?: boolean;
  showBatchActions?: boolean;
  onNotificationClick?: (notification: Notification) => void;
}

const NotificationList: React.FC<NotificationListProps> = ({
  height = 600,
  showFilters = true,
  showBatchActions = true,
  onNotificationClick
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  const [filters, setFilters] = useState<NotificationQuery>({
    page: 1,
    size: 20
  });
  const [showFilterPanel, setShowFilterPanel] = useState(false);

  // 加载通知列表
  const loadNotifications = async () => {
    try {
      setLoading(true);
      const response = await notificationService.getNotifications({
        ...filters,
        page: currentPage,
        size: pageSize
      });
      setNotifications(response.items);
      setTotal(response.total);
    } catch (error) {
      message.error('加载通知列表失败');
      console.error('Load notifications error:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [currentPage, filters]);

  // 标记为已读
  const handleMarkAsRead = async (id: number) => {
    try {
      await notificationService.markAsRead(id);
      message.success('已标记为已读');
      loadNotifications();
    } catch (error) {
      message.error('标记失败');
    }
  };

  // 删除通知
  const handleDelete = async (id: number) => {
    try {
      await notificationService.deleteNotification(id);
      message.success('删除成功');
      loadNotifications();
    } catch (error) {
      message.error('删除失败');
    }
  };

  // 批量标记为已读
  const handleBatchMarkAsRead = async () => {
    if (selectedIds.length === 0) {
      message.warning('请选择要操作的通知');
      return;
    }

    try {
      await notificationService.markMultipleAsRead(selectedIds);
      message.success(`已标记 ${selectedIds.length} 条通知为已读`);
      setSelectedIds([]);
      loadNotifications();
    } catch (error) {
      message.error('批量标记失败');
    }
  };

  // 批量删除
  const handleBatchDelete = async () => {
    if (selectedIds.length === 0) {
      message.warning('请选择要删除的通知');
      return;
    }

    try {
      await notificationService.deleteMultiple(selectedIds);
      message.success(`已删除 ${selectedIds.length} 条通知`);
      setSelectedIds([]);
      loadNotifications();
    } catch (error) {
      message.error('批量删除失败');
    }
  };

  // 导出通知
  const handleExport = async () => {
    try {
      const blob = await notificationService.exportNotifications(filters);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `notifications_${new Date().toISOString().split('T')[0]}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success('导出成功');
    } catch (error) {
      message.error('导出失败');
    }
  };

  // 应用筛选
  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      page: 1
    }));
    setCurrentPage(1);
  };

  // 重置筛选
  const handleResetFilters = () => {
    setFilters({ page: 1, size: pageSize });
    setCurrentPage(1);
  };

  // 全选/取消全选
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(notifications.map(n => n.id));
    } else {
      setSelectedIds([]);
    }
  };

  // 单选
  const handleSelectItem = (id: number, checked: boolean) => {
    if (checked) {
      setSelectedIds(prev => [...prev, id]);
    } else {
      setSelectedIds(prev => prev.filter(selectedId => selectedId !== id));
    }
  };

  // 获取通知图标
  const getNotificationIcon = (type: NotificationType) => {
    return (
      <BellOutlined 
        style={{ 
          color: NOTIFICATION_TYPE_COLORS[type],
          fontSize: '16px'
        }} 
      />
    );
  };

  // 渲染通知项
  const renderNotificationItem = (notification: Notification) => {
    const isUnread = notification.status !== NotificationStatus.READ;
    
    return (
      <List.Item
        key={notification.id}
        style={{
          backgroundColor: isUnread ? '#f6ffed' : 'white',
          border: isUnread ? '1px solid #b7eb8f' : '1px solid #f0f0f0',
          borderRadius: '6px',
          marginBottom: '8px',
          padding: '12px 16px'
        }}
        actions={[
          <Tooltip title="查看详情">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => onNotificationClick?.(notification)}
            />
          </Tooltip>,
          notification.status !== NotificationStatus.READ && (
            <Tooltip title="标记为已读">
              <Button
                type="text"
                icon={<CheckOutlined />}
                onClick={() => handleMarkAsRead(notification.id)}
              />
            </Tooltip>
          ),
          <Popconfirm
            title="确定要删除这条通知吗？"
            onConfirm={() => handleDelete(notification.id)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="删除">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        ]}
      >
        <List.Item.Meta
          avatar={
            <Space>
              {showBatchActions && (
                <Checkbox
                  checked={selectedIds.includes(notification.id)}
                  onChange={(e) => handleSelectItem(notification.id, e.target.checked)}
                />
              )}
              {getNotificationIcon(notification.notification_type)}
              {isUnread && <Badge dot />}
            </Space>
          }
          title={
            <Space>
              <Text strong={isUnread}>{notification.title}</Text>
              <Tag color={NOTIFICATION_PRIORITY_COLORS[notification.priority]}>
                {NOTIFICATION_PRIORITY_LABELS[notification.priority]}
              </Tag>
              <Tag color={NOTIFICATION_TYPE_COLORS[notification.notification_type]}>
                {NOTIFICATION_TYPE_LABELS[notification.notification_type]}
              </Tag>
              <Tag color={NOTIFICATION_STATUS_COLORS[notification.status]}>
                {NOTIFICATION_STATUS_LABELS[notification.status]}
              </Tag>
            </Space>
          }
          description={
            <Space direction="vertical" size={4}>
              <Paragraph
                ellipsis={{ rows: 2, expandable: true }}
                style={{ margin: 0, color: isUnread ? '#000' : '#666' }}
              >
                {notification.content}
              </Paragraph>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {new Date(notification.created_at).toLocaleString()}
                {notification.read_at && (
                  <span style={{ marginLeft: '8px' }}>
                    • 已读于 {new Date(notification.read_at).toLocaleString()}
                  </span>
                )}
              </Text>
            </Space>
          }
        />
      </List.Item>
    );
  };

  return (
    <Card
      title={
        <Space>
          <BellOutlined />
          <span>通知列表</span>
          <Badge count={notifications.filter(n => n.status !== NotificationStatus.READ).length} />
        </Space>
      }
      extra={
        <Space>
          {showFilters && (
            <Button
              icon={<FilterOutlined />}
              onClick={() => setShowFilterPanel(!showFilterPanel)}
            >
              筛选
            </Button>
          )}
          <Button icon={<ReloadOutlined />} onClick={loadNotifications}>
            刷新
          </Button>
          <Button icon={<ExportOutlined />} onClick={handleExport}>
            导出
          </Button>
        </Space>
      }
      bodyStyle={{ padding: 0 }}
    >
      {/* 筛选面板 */}
      {showFilters && showFilterPanel && (
        <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0' }}>
          <Row gutter={[16, 16]}>
            <Col span={6}>
              <Search
                placeholder="搜索通知内容"
                onSearch={(value) => handleFilterChange('search', value)}
                allowClear
              />
            </Col>
            <Col span={4}>
              <Select
                placeholder="通知类型"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilterChange('notification_type', value)}
              >
                {Object.entries(NOTIFICATION_TYPE_LABELS).map(([key, label]) => (
                  <Option key={key} value={key}>{label}</Option>
                ))}
              </Select>
            </Col>
            <Col span={4}>
              <Select
                placeholder="优先级"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilterChange('priority', value)}
              >
                {Object.entries(NOTIFICATION_PRIORITY_LABELS).map(([key, label]) => (
                  <Option key={key} value={key}>{label}</Option>
                ))}
              </Select>
            </Col>
            <Col span={4}>
              <Select
                placeholder="状态"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilterChange('status', value)}
              >
                {Object.entries(NOTIFICATION_STATUS_LABELS).map(([key, label]) => (
                  <Option key={key} value={key}>{label}</Option>
                ))}
              </Select>
            </Col>
            <Col span={6}>
              <RangePicker
                style={{ width: '100%' }}
                onChange={(dates) => {
                  if (dates) {
                    handleFilterChange('start_date', dates[0]?.toISOString());
                    handleFilterChange('end_date', dates[1]?.toISOString());
                  } else {
                    handleFilterChange('start_date', undefined);
                    handleFilterChange('end_date', undefined);
                  }
                }}
              />
            </Col>
          </Row>
          <Row style={{ marginTop: '16px' }}>
            <Col>
              <Button onClick={handleResetFilters}>重置筛选</Button>
            </Col>
          </Row>
        </div>
      )}

      {/* 批量操作栏 */}
      {showBatchActions && (
        <div style={{ padding: '16px', borderBottom: '1px solid #f0f0f0' }}>
          <Space>
            <Checkbox
              indeterminate={selectedIds.length > 0 && selectedIds.length < notifications.length}
              checked={selectedIds.length === notifications.length && notifications.length > 0}
              onChange={(e) => handleSelectAll(e.target.checked)}
            >
              全选
            </Checkbox>
            <Text type="secondary">已选择 {selectedIds.length} 项</Text>
            <Button
              disabled={selectedIds.length === 0}
              onClick={handleBatchMarkAsRead}
            >
              批量标记已读
            </Button>
            <Popconfirm
              title={`确定要删除选中的 ${selectedIds.length} 条通知吗？`}
              onConfirm={handleBatchDelete}
              disabled={selectedIds.length === 0}
            >
              <Button danger disabled={selectedIds.length === 0}>
                批量删除
              </Button>
            </Popconfirm>
          </Space>
        </div>
      )}

      {/* 通知列表 */}
      <div style={{ height: height - 120, overflow: 'auto', padding: '16px' }}>
        <Spin spinning={loading}>
          {notifications.length > 0 ? (
            <List
              dataSource={notifications}
              renderItem={renderNotificationItem}
              pagination={{
                current: currentPage,
                pageSize,
                total,
                showSizeChanger: false,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
                onChange: (page) => setCurrentPage(page)
              }}
            />
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="暂无通知"
            />
          )}
        </Spin>
      </div>
    </Card>
  );
};

export default NotificationList;