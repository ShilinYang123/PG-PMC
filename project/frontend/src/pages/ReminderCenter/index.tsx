/**
 * 催办中心页面
 * 
 * 功能包括：
 * - 催办记录列表
 * - 催办统计分析
 * - 催办规则管理
 * - 快捷催办操作
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  DatePicker,
  Statistic,
  Row,
  Col,
  Tabs,
  Badge,
  Tooltip,
  message,
  Popconfirm,
  Progress,
  Timeline,
  Descriptions,
  Alert
} from 'antd';
import {
  BellOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
  PlusOutlined,
  SettingOutlined,
  BarChartOutlined,
  SendOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { ColumnsType } from 'antd/es/table';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';

// 配置dayjs
dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

const { TabPane } = Tabs;
const { Option } = Select;
const { TextArea } = Input;

// 类型定义
interface ReminderRecord {
  record_id: string;
  reminder_type: string;
  related_type: string;
  related_id: number;
  reminder_level: number;
  recipients: number[];
  sent_at: string;
  response_deadline: string;
  is_responded: boolean;
  response_time?: string;
  escalated: boolean;
}

interface ReminderStatistics {
  total_reminders: number;
  responded_reminders: number;
  escalated_reminders: number;
  pending_reminders: number;
  response_rate: number;
  escalation_rate: number;
  avg_response_time_hours: number;
  type_statistics: Record<string, { total: number; responded: number; escalated: number }>;
}

interface ReminderRule {
  rule_id: string;
  name: string;
  reminder_type: string;
  trigger_conditions: Record<string, any>;
  reminder_intervals: number[];
  escalation_rules: Record<string, any>;
  notification_types: string[];
  is_active: boolean;
}

const ReminderCenter: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [reminders, setReminders] = useState<ReminderRecord[]>([]);
  const [statistics, setStatistics] = useState<ReminderStatistics | null>(null);
  const [rules, setRules] = useState<ReminderRule[]>([]);
  const [selectedReminder, setSelectedReminder] = useState<ReminderRecord | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [activeTab, setActiveTab] = useState('list');
  const [filters, setFilters] = useState({
    reminder_type: undefined,
    is_responded: undefined,
    escalated: undefined
  });
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });

  const [form] = Form.useForm();

  // 催办类型映射
  const reminderTypeMap = {
    'order_due': { label: '订单交期', color: 'orange', icon: <ClockCircleOutlined /> },
    'task_overdue': { label: '任务逾期', color: 'red', icon: <ExclamationCircleOutlined /> },
    'quality_issue': { label: '质量问题', color: 'volcano', icon: <WarningOutlined /> },
    'equipment_maintenance': { label: '设备维护', color: 'blue', icon: <SettingOutlined /> },
    'material_shortage': { label: '物料短缺', color: 'purple', icon: <ExclamationCircleOutlined /> },
    'progress_delay': { label: '进度延迟', color: 'gold', icon: <ClockCircleOutlined /> }
  };

  // 催办级别映射
  const reminderLevelMap = {
    1: { label: '首次催办', color: 'blue' },
    2: { label: '二次催办', color: 'orange' },
    3: { label: '三次催办', color: 'red' },
    4: { label: '升级催办', color: 'volcano' }
  };

  // 获取催办记录列表
  const fetchReminders = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: pagination.current.toString(),
        page_size: pagination.pageSize.toString(),
        ...Object.fromEntries(
          Object.entries(filters).filter(([_, value]) => value !== undefined)
        )
      });

      const response = await fetch(`/api/reminders/list?${params}`);
      const result = await response.json();

      if (result.success) {
        setReminders(result.data);
        setPagination(prev => ({
          ...prev,
          total: result.total
        }));
      } else {
        message.error(result.message || '获取催办记录失败');
      }
    } catch (error) {
      console.error('获取催办记录失败:', error);
      message.error('获取催办记录失败');
    } finally {
      setLoading(false);
    }
  };

  // 获取催办统计
  const fetchStatistics = async () => {
    try {
      const response = await fetch('/api/reminders/statistics');
      const result = await response.json();

      if (result.success) {
        setStatistics(result.data);
      } else {
        message.error(result.message || '获取催办统计失败');
      }
    } catch (error) {
      console.error('获取催办统计失败:', error);
      message.error('获取催办统计失败');
    }
  };

  // 获取催办规则
  const fetchRules = async () => {
    try {
      const response = await fetch('/api/reminders/rules');
      const result = await response.json();

      if (result.success) {
        setRules(result.data);
      } else {
        message.error(result.message || '获取催办规则失败');
      }
    } catch (error) {
      console.error('获取催办规则失败:', error);
      message.error('获取催办规则失败');
    }
  };

  // 响应催办
  const handleRespond = async (recordId: string) => {
    try {
      const response = await fetch('/api/reminders/respond', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          record_id: recordId,
          response_time: new Date().toISOString()
        })
      });

      const result = await response.json();

      if (result.success) {
        message.success('催办响应成功');
        fetchReminders();
        fetchStatistics();
      } else {
        message.error(result.message || '催办响应失败');
      }
    } catch (error) {
      console.error('催办响应失败:', error);
      message.error('催办响应失败');
    }
  };

  // 手动处理待催办
  const handleProcessPending = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/reminders/process-pending', {
        method: 'POST'
      });

      const result = await response.json();

      if (result.success) {
        message.success(`成功处理 ${result.data} 个待催办记录`);
        fetchReminders();
        fetchStatistics();
      } else {
        message.error(result.message || '处理待催办失败');
      }
    } catch (error) {
      console.error('处理待催办失败:', error);
      message.error('处理待催办失败');
    } finally {
      setLoading(false);
    }
  };

  // 创建催办
  const handleCreateReminder = async (values: any) => {
    try {
      const response = await fetch('/api/reminders/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(values)
      });

      const result = await response.json();

      if (result.success) {
        message.success('催办创建成功');
        setCreateModalVisible(false);
        form.resetFields();
        fetchReminders();
        fetchStatistics();
      } else {
        message.error(result.message || '催办创建失败');
      }
    } catch (error) {
      console.error('催办创建失败:', error);
      message.error('催办创建失败');
    }
  };

  // 表格列定义
  const columns: ColumnsType<ReminderRecord> = [
    {
      title: '催办类型',
      dataIndex: 'reminder_type',
      key: 'reminder_type',
      width: 120,
      render: (type: string) => {
        const typeInfo = reminderTypeMap[type as keyof typeof reminderTypeMap];
        return (
          <Tag color={typeInfo?.color} icon={typeInfo?.icon}>
            {typeInfo?.label || type}
          </Tag>
        );
      },
      filters: Object.entries(reminderTypeMap).map(([value, { label }]) => ({
        text: label,
        value
      })),
      onFilter: (value, record) => record.reminder_type === value
    },
    {
      title: '催办级别',
      dataIndex: 'reminder_level',
      key: 'reminder_level',
      width: 100,
      render: (level: number) => {
        const levelInfo = reminderLevelMap[level as keyof typeof reminderLevelMap];
        return (
          <Tag color={levelInfo?.color}>
            {levelInfo?.label || `级别${level}`}
          </Tag>
        );
      }
    },
    {
      title: '关联对象',
      key: 'related',
      width: 120,
      render: (_, record) => (
        <span>
          {record.related_type}#{record.related_id}
        </span>
      )
    },
    {
      title: '发送时间',
      dataIndex: 'sent_at',
      key: 'sent_at',
      width: 150,
      render: (time: string) => (
        <Tooltip title={dayjs(time).format('YYYY-MM-DD HH:mm:ss')}>
          {dayjs(time).fromNow()}
        </Tooltip>
      ),
      sorter: (a, b) => dayjs(a.sent_at).unix() - dayjs(b.sent_at).unix()
    },
    {
      title: '响应期限',
      dataIndex: 'response_deadline',
      key: 'response_deadline',
      width: 150,
      render: (deadline: string, record) => {
        const isOverdue = dayjs().isAfter(dayjs(deadline)) && !record.is_responded;
        return (
          <span style={{ color: isOverdue ? '#ff4d4f' : undefined }}>
            <Tooltip title={dayjs(deadline).format('YYYY-MM-DD HH:mm:ss')}>
              {dayjs(deadline).fromNow()}
            </Tooltip>
            {isOverdue && <WarningOutlined style={{ marginLeft: 4, color: '#ff4d4f' }} />}
          </span>
        );
      }
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_, record) => {
        if (record.escalated) {
          return <Badge status="error" text="已升级" />;
        }
        if (record.is_responded) {
          return <Badge status="success" text="已响应" />;
        }
        return <Badge status="processing" text="待响应" />;
      },
      filters: [
        { text: '已响应', value: 'responded' },
        { text: '待响应', value: 'pending' },
        { text: '已升级', value: 'escalated' }
      ],
      onFilter: (value, record) => {
        if (value === 'responded') return record.is_responded;
        if (value === 'escalated') return record.escalated;
        if (value === 'pending') return !record.is_responded && !record.escalated;
        return true;
      }
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => {
              setSelectedReminder(record);
              setDetailModalVisible(true);
            }}
          >
            详情
          </Button>
          {!record.is_responded && !record.escalated && (
            <Popconfirm
              title="确认响应此催办？"
              onConfirm={() => handleRespond(record.record_id)}
              okText="确认"
              cancelText="取消"
            >
              <Button
                type="link"
                size="small"
                icon={<CheckCircleOutlined />}
                style={{ color: '#52c41a' }}
              >
                响应
              </Button>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ];

  // 统计卡片
  const renderStatisticsCards = () => {
    if (!statistics) return null;

    return (
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="总催办数"
              value={statistics.total_reminders}
              prefix={<BellOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="已响应"
              value={statistics.responded_reminders}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="待响应"
              value={statistics.pending_reminders}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="响应率"
              value={statistics.response_rate}
              suffix="%"
              prefix={<BarChartOutlined />}
              valueStyle={{ color: statistics.response_rate >= 80 ? '#3f8600' : '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // 催办详情模态框
  const renderDetailModal = () => {
    if (!selectedReminder) return null;

    const typeInfo = reminderTypeMap[selectedReminder.reminder_type as keyof typeof reminderTypeMap];
    const levelInfo = reminderLevelMap[selectedReminder.reminder_level as keyof typeof reminderLevelMap];

    return (
      <Modal
        title="催办详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>,
          !selectedReminder.is_responded && !selectedReminder.escalated && (
            <Button
              key="respond"
              type="primary"
              icon={<CheckCircleOutlined />}
              onClick={() => {
                handleRespond(selectedReminder.record_id);
                setDetailModalVisible(false);
              }}
            >
              标记已响应
            </Button>
          )
        ].filter(Boolean)}
        width={600}
      >
        <Descriptions column={2} bordered>
          <Descriptions.Item label="催办ID" span={2}>
            {selectedReminder.record_id}
          </Descriptions.Item>
          <Descriptions.Item label="催办类型">
            <Tag color={typeInfo?.color} icon={typeInfo?.icon}>
              {typeInfo?.label || selectedReminder.reminder_type}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="催办级别">
            <Tag color={levelInfo?.color}>
              {levelInfo?.label || `级别${selectedReminder.reminder_level}`}
            </Tag>
          </Descriptions.Item>
          <Descriptions.Item label="关联对象">
            {selectedReminder.related_type}#{selectedReminder.related_id}
          </Descriptions.Item>
          <Descriptions.Item label="接收人数">
            {selectedReminder.recipients.length} 人
          </Descriptions.Item>
          <Descriptions.Item label="发送时间">
            {dayjs(selectedReminder.sent_at).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="响应期限">
            {dayjs(selectedReminder.response_deadline).format('YYYY-MM-DD HH:mm:ss')}
          </Descriptions.Item>
          <Descriptions.Item label="当前状态" span={2}>
            {selectedReminder.escalated ? (
              <Badge status="error" text="已升级" />
            ) : selectedReminder.is_responded ? (
              <Badge status="success" text="已响应" />
            ) : (
              <Badge status="processing" text="待响应" />
            )}
          </Descriptions.Item>
          {selectedReminder.response_time && (
            <Descriptions.Item label="响应时间" span={2}>
              {dayjs(selectedReminder.response_time).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          )}
        </Descriptions>
      </Modal>
    );
  };

  // 创建催办模态框
  const renderCreateModal = () => {
    return (
      <Modal
        title="创建催办"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateReminder}
        >
          <Form.Item
            name="reminder_type"
            label="催办类型"
            rules={[{ required: true, message: '请选择催办类型' }]}
          >
            <Select placeholder="请选择催办类型">
              {Object.entries(reminderTypeMap).map(([value, { label }]) => (
                <Option key={value} value={value}>
                  {label}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="related_type"
            label="关联对象类型"
            rules={[{ required: true, message: '请输入关联对象类型' }]}
          >
            <Input placeholder="如：order, task, equipment" />
          </Form.Item>
          
          <Form.Item
            name="related_id"
            label="关联对象ID"
            rules={[{ required: true, message: '请输入关联对象ID' }]}
          >
            <Input type="number" placeholder="请输入关联对象ID" />
          </Form.Item>
          
          <Form.Item
            name="data"
            label="催办数据（JSON格式）"
            rules={[{ required: true, message: '请输入催办数据' }]}
          >
            <TextArea
              rows={4}
              placeholder='例如：{"responsible_user_id": 1, "description": "催办描述"}'
            />
          </Form.Item>
        </Form>
      </Modal>
    );
  };

  useEffect(() => {
    fetchReminders();
    fetchStatistics();
    fetchRules();
  }, [pagination.current, pagination.pageSize, filters]);

  return (
    <div style={{ padding: 24 }}>
      <Card title="催办中心" style={{ marginBottom: 24 }}>
        <Space style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            创建催办
          </Button>
          <Button
            icon={<SendOutlined />}
            onClick={handleProcessPending}
            loading={loading}
          >
            处理待催办
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              fetchReminders();
              fetchStatistics();
            }}
          >
            刷新
          </Button>
        </Space>

        {renderStatisticsCards()}

        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="催办列表" key="list">
            <Table
              columns={columns}
              dataSource={reminders}
              rowKey="record_id"
              loading={loading}
              pagination={{
                ...pagination,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
              }}
              onChange={(pag, filters) => {
                setPagination(prev => ({
                  ...prev,
                  current: pag.current || 1,
                  pageSize: pag.pageSize || 20
                }));
              }}
            />
          </TabPane>
          
          <TabPane tab="统计分析" key="statistics">
            {statistics && (
              <div>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Card title="响应率分析">
                      <Progress
                        type="circle"
                        percent={statistics.response_rate}
                        format={percent => `${percent}%`}
                        status={statistics.response_rate >= 80 ? 'success' : 'exception'}
                      />
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card title="升级率分析">
                      <Progress
                        type="circle"
                        percent={statistics.escalation_rate}
                        format={percent => `${percent}%`}
                        status={statistics.escalation_rate <= 10 ? 'success' : 'exception'}
                      />
                    </Card>
                  </Col>
                </Row>
                
                <Card title="按类型统计" style={{ marginTop: 16 }}>
                  <Row gutter={[16, 16]}>
                    {Object.entries(statistics.type_statistics).map(([type, stats]) => {
                      const typeInfo = reminderTypeMap[type as keyof typeof reminderTypeMap];
                      return (
                        <Col key={type} xs={24} sm={12} md={8} lg={6}>
                          <Card size="small">
                            <Statistic
                              title={typeInfo?.label || type}
                              value={stats.total}
                              prefix={typeInfo?.icon}
                              suffix={`(${stats.responded}已响应)`}
                            />
                          </Card>
                        </Col>
                      );
                    })}
                  </Row>
                </Card>
              </div>
            )}
          </TabPane>
          
          <TabPane tab="催办规则" key="rules">
            <Alert
              message="催办规则管理"
              description="以下是系统中配置的催办规则，用于自动触发催办通知。"
              type="info"
              style={{ marginBottom: 16 }}
            />
            <Table
              dataSource={rules}
              rowKey="rule_id"
              columns={[
                {
                  title: '规则名称',
                  dataIndex: 'name',
                  key: 'name'
                },
                {
                  title: '催办类型',
                  dataIndex: 'reminder_type',
                  key: 'reminder_type',
                  render: (type: string) => {
                    const typeInfo = reminderTypeMap[type as keyof typeof reminderTypeMap];
                    return (
                      <Tag color={typeInfo?.color} icon={typeInfo?.icon}>
                        {typeInfo?.label || type}
                      </Tag>
                    );
                  }
                },
                {
                  title: '催办间隔',
                  dataIndex: 'reminder_intervals',
                  key: 'reminder_intervals',
                  render: (intervals: number[]) => (
                    <span>{intervals.join(', ')} 小时</span>
                  )
                },
                {
                  title: '通知方式',
                  dataIndex: 'notification_types',
                  key: 'notification_types',
                  render: (types: string[]) => (
                    <Space>
                      {types.map(type => (
                        <Tag key={type}>{type}</Tag>
                      ))}
                    </Space>
                  )
                },
                {
                  title: '状态',
                  dataIndex: 'is_active',
                  key: 'is_active',
                  render: (active: boolean) => (
                    <Badge
                      status={active ? 'success' : 'default'}
                      text={active ? '启用' : '禁用'}
                    />
                  )
                }
              ]}
            />
          </TabPane>
        </Tabs>
      </Card>

      {renderDetailModal()}
      {renderCreateModal()}
    </div>
  );
};

export default ReminderCenter;