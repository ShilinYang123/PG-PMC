import React, { useState } from 'react';
import {
  Form,
  Input,
  Button,
  Card,
  message,
  Checkbox,
  Divider,
  Space,
  Typography,
  Row,
  Col,
  Alert
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone,
  SafetyOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import './index.css';

const { Title, Text } = Typography;

interface LoginForm {
  username: string;
  password: string;
  remember: boolean;
  captcha?: string;
}

const Login: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [showCaptcha, setShowCaptcha] = useState(false);
  const navigate = useNavigate();
  const { login, isLoading } = useAuthStore();

  const handleSubmit = async (values: LoginForm) => {
    try {
      setLoading(true);
      await login({
        username: values.username,
        password: values.password,
        remember_me: values.remember
      });
      
      message.success('登录成功！');
      navigate('/dashboard');
    } catch (error: any) {
      console.error('登录失败:', error);
      
      // 处理不同的错误情况
      if (error.response?.status === 401) {
        message.error('用户名或密码错误');
      } else if (error.response?.status === 423) {
        message.error('账户已被锁定，请联系管理员');
      } else if (error.response?.status === 429) {
        message.error('登录尝试过于频繁，请稍后再试');
        setShowCaptcha(true);
      } else {
        message.error(error.message || '登录失败，请稍后重试');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = () => {
    message.info('密码重置功能正在开发中，请联系管理员');
  };

  return (
    <div className="login-container">
      <div className="login-background">
        <div className="login-content">
          <Row justify="center" align="middle" style={{ minHeight: '100vh' }}>
            <Col xs={22} sm={16} md={12} lg={8} xl={6}>
              <Card className="login-card" bordered={false}>
                <div className="login-header">
                  <div className="logo">
                    <SafetyOutlined style={{ fontSize: 48, color: '#1890ff' }} />
                  </div>
                  <Title level={2} className="login-title">
                    PMC管理系统
                  </Title>
                  <Text type="secondary" className="login-subtitle">
                    生产计划与物料控制全流程管理平台
                  </Text>
                </div>

                <Divider />

                <Form
                  form={form}
                  name="login"
                  onFinish={handleSubmit}
                  autoComplete="off"
                  size="large"
                >
                  <Form.Item
                    name="username"
                    rules={[
                      { required: true, message: '请输入用户名' },
                      { min: 3, message: '用户名至少3个字符' },
                      { max: 50, message: '用户名不能超过50个字符' }
                    ]}
                  >
                    <Input
                      prefix={<UserOutlined />}
                      placeholder="用户名"
                      autoComplete="username"
                    />
                  </Form.Item>

                  <Form.Item
                    name="password"
                    rules={[
                      { required: true, message: '请输入密码' },
                      { min: 6, message: '密码至少6个字符' }
                    ]}
                  >
                    <Input.Password
                      prefix={<LockOutlined />}
                      placeholder="密码"
                      autoComplete="current-password"
                      iconRender={(visible) => (visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />)}
                    />
                  </Form.Item>

                  {showCaptcha && (
                    <Form.Item
                      name="captcha"
                      rules={[{ required: true, message: '请输入验证码' }]}
                    >
                      <Row gutter={8}>
                        <Col span={14}>
                          <Input placeholder="验证码" />
                        </Col>
                        <Col span={10}>
                          <div className="captcha-image">
                            <img 
                              src="/api/v1/auth/captcha" 
                              alt="验证码" 
                              style={{ width: '100%', height: 40, cursor: 'pointer' }}
                              onClick={() => window.location.reload()}
                            />
                          </div>
                        </Col>
                      </Row>
                    </Form.Item>
                  )}

                  <Form.Item>
                    <Row justify="space-between" align="middle">
                      <Col>
                        <Form.Item name="remember" valuePropName="checked" noStyle>
                          <Checkbox>记住我</Checkbox>
                        </Form.Item>
                      </Col>
                      <Col>
                        <Button type="link" onClick={handleForgotPassword}>
                          忘记密码？
                        </Button>
                      </Col>
                    </Row>
                  </Form.Item>

                  <Form.Item>
                    <Button
                      type="primary"
                      htmlType="submit"
                      loading={loading || isLoading}
                      block
                      size="large"
                    >
                      登录
                    </Button>
                  </Form.Item>
                </Form>

                <Divider plain>
                  <Text type="secondary">其他登录方式</Text>
                </Divider>

                <div className="login-footer">
                  <Space direction="vertical" align="center" style={{ width: '100%' }}>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      如需帮助，请联系系统管理员
                    </Text>
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      © 2024 PMC管理系统. All rights reserved.
                    </Text>
                  </Space>
                </div>
              </Card>
            </Col>
          </Row>
        </div>
      </div>
    </div>
  );
};

export default Login;