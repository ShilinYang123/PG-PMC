import React, { useState, useEffect } from 'react';
import {
  Layout,
  Card,
  Tabs,
  Button,
  Space,
  message,
  Modal,
  Badge,
  Tooltip,
  FloatButton
} from 'antd';
import {
  BellOutlined,
  PlusOutlined,
  SettingOutlined,
  BarChartOutlined,
  ReloadOutlined,
  NotificationOutlined
} from '@ant-design/icons';
import NotificationList from '../../components/Notifications/NotificationList';
import NotificationDetail from '../../components/Notifications/NotificationDetail';
import NotificationStats from '../../components/Notifications/NotificationStats';
import {
  Notification,
  NotificationStats as INotificationStats
} from '../../types/notification';
import notificationService from '../../services/notificationService';

const { Content } = Layout;
const { TabPane } = Tabs;

interface NotificationCenterProps {
  // 可以接收外部传入的配置
}

const NotificationCenter: React.FC<NotificationCenterProps> = () => {
  const [activeTab, setActiveTab] = useState('list');
  const [selectedNotification, setSelectedNotification] = useState<Notification | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [stats, setStats] = useState<INotificationStats | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [realTimeConnection, setRealTimeConnection] = useState<EventSource | null>(null);

  // 初始化实时通知连接
  useEffect(() => {
    const initRealTimeConnection = async () => {
      try {
        // 假设用户ID从认证状态获取
        const userId = 1; // 这里应该从用户认证状态获取
        
        const eventSource = await notificationService.subscribeToNotifications(
          userId,
          (notification: Notification) => {
            // 收到新通知时的处理
            message.info({
              content: (
                <div>
                  <strong>{notification.title}</strong>
                  <br />
                  {notification.content.substring(0, 50)}...
                </div>
              ),
              duration: 5,
              icon: <BellOutlined style={{ color: '#1890ff' }} />
            });
            
            // 刷新列表
            setRefreshKey(prev => prev + 1);
          }
        );
        
        setRealTimeConnection(eventSource);
      } catch (error) {
        console.error('Failed to initialize real-time connection:', error);
      }
    };

    initRealTimeConnection();

    // 清理连接
    return () => {
      if (realTimeConnection) {
        realTimeConnection.close();
      }
    };
  }, []);

  // 处理通知点击
  const handleNotificationClick = (notification: Notification) => {
    setSelectedNotification(notification);
    setDetailVisible(true);
  };

  // 处理详情关闭
  const handleDetailClose = () => {
    setDetailVisible(false);
    setSelectedNotification(null);
  };

  // 处理通知更新
  const handleNotificationUpdate = () => {
    setRefreshKey(prev => prev + 1);
  };

  // 处理统计数据变化
  const handleStatsChange = (newStats: INotificationStats) => {
    setStats(newStats);
  };

  // 刷新所有数据
  const handleRefreshAll = () => {
    setRefreshKey(prev => prev + 1);
    message.success('数据已刷新');
  };

  // 创建新通知（管理员功能）
  const handleCreateNotification = () => {
    Modal.info({
      title: '创建通知',
      content: '此功能正在开发中，敬请期待！',
      okText: '确定'
    });
  };

  // 通知设置
  const handleNotificationSettings = () => {
    Modal.info({
      title: '通知设置',
      content: '此功能正在开发中，敬请期待！',
      okText: '确定'
    });
  };

  return (
    <Layout style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      <Content style={{ padding: '24px' }}>
        <Card
          title={
            <Space>
              <NotificationOutlined />
              <span>通知中心</span>
              {stats && stats.unread_count > 0 && (
                <Badge count={stats.unread_count} />
              )}
            </Space>
          }
          extra={
            <Space>
              <Tooltip title="刷新数据">
                <Button
                  type="text"
                  icon={<ReloadOutlined />}
                  onClick={handleRefreshAll}
                >
                  刷新
                </Button>
              </Tooltip>
              <Tooltip title="通知设置">
                <Button
                  type="text"
                  icon={<SettingOutlined />}
                  onClick={handleNotificationSettings}
                >
                  设置
                </Button>
              </Tooltip>
              <Button
                type="primary"
                icon={<PlusOutlined />}
                onClick={handleCreateNotification}
              >
                创建通知
              </Button>
            </Space>
          }
          bodyStyle={{ padding: 0 }}
        >
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            style={{ padding: '0 24px' }}
            items={[
              {
                key: 'list',
                label: (
                  <Space>
                    <BellOutlined />
                    <span>通知列表</span>
                    {stats && stats.unread_count > 0 && (
                      <Badge count={stats.unread_count} size="small" />
                    )}
                  </Space>
                ),
                children: (
                  <div style={{ padding: '24px 0' }}>
                    <NotificationList
                      key={refreshKey}
                      height={600}
                      showFilters={true}
                      showBatchActions={true}
                      onNotificationClick={handleNotificationClick}
                    />
                  </div>
                )
              },
              {
                key: 'stats',
                label: (
                  <Space>
                    <BarChartOutlined />
                    <span>统计分析</span>
                  </Space>
                ),
                children: (
                  <div style={{ padding: '24px 0' }}>
                    <NotificationStats
                      key={refreshKey}
                      isAdmin={false} // 这里应该根据用户权限设置
                      refreshInterval={30000}
                      onStatsChange={handleStatsChange}
                    />
                  </div>
                )
              }
            ]}
          />
        </Card>

        {/* 通知详情弹窗 */}
        <NotificationDetail
          notification={selectedNotification || undefined}
          visible={detailVisible}
          onClose={handleDetailClose}
          onUpdate={handleNotificationUpdate}
          showActions={true}
        />

        {/* 浮动按钮 */}
        <FloatButton.Group
          trigger="hover"
          type="primary"
          style={{ right: 24 }}
          icon={<BellOutlined />}
        >
          <FloatButton
            icon={<ReloadOutlined />}
            tooltip="刷新通知"
            onClick={handleRefreshAll}
          />
          <FloatButton
            icon={<SettingOutlined />}
            tooltip="通知设置"
            onClick={handleNotificationSettings}
          />
          <FloatButton
            icon={<PlusOutlined />}
            tooltip="创建通知"
            onClick={handleCreateNotification}
          />
        </FloatButton.Group>

        {/* 未读通知提醒 */}
        {stats && stats.unread_count > 0 && (
          <div
            style={{
              position: 'fixed',
              top: '50%',
              right: '24px',
              transform: 'translateY(-50%)',
              zIndex: 1000
            }}
          >
            <Card
              size="small"
              style={{
                width: '200px',
                backgroundColor: '#fff7e6',
                border: '1px solid #ffd591',
                boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)'
              }}
              bodyStyle={{ padding: '12px' }}
            >
              <Space direction="vertical" size={4}>
                <Space>
                  <BellOutlined style={{ color: '#fa8c16' }} />
                  <span style={{ fontSize: '12px', fontWeight: 'bold' }}>
                    未读通知
                  </span>
                </Space>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#fa8c16' }}>
                  {stats.unread_count}
                </div>
                <Button
                  size="small"
                  type="link"
                  onClick={() => setActiveTab('list')}
                  style={{ padding: 0, height: 'auto' }}
                >
                  查看详情
                </Button>
              </Space>
            </Card>
          </div>
        )}
      </Content>
    </Layout>
  );
};

export default NotificationCenter;