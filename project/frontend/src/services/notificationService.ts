import axios from 'axios';
import {
  Notification,
  NotificationTemplate,
  NotificationRule,
  NotificationStats,
  NotificationQuery,
  NotificationCreate,
  NotificationUpdate,
  BatchNotificationCreate
} from '../types/notification';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

class NotificationService {
  private baseURL = `${API_BASE_URL}/notifications`;

  // 通知相关方法
  async createNotification(notification: NotificationCreate): Promise<Notification> {
    const response = await axios.post(`${this.baseURL}/`, notification);
    return response.data;
  }

  async createBatchNotifications(batchData: BatchNotificationCreate): Promise<Notification[]> {
    const response = await axios.post(`${this.baseURL}/batch`, batchData);
    return response.data;
  }

  async getNotifications(query?: NotificationQuery): Promise<{
    items: Notification[];
    total: number;
    page: number;
    size: number;
    pages: number;
  }> {
    const params = new URLSearchParams();
    
    if (query) {
      Object.entries(query).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }

    const response = await axios.get(`${this.baseURL}/?${params.toString()}`);
    return response.data;
  }

  async getNotification(id: number): Promise<Notification> {
    const response = await axios.get(`${this.baseURL}/${id}`);
    return response.data;
  }

  async updateNotification(id: number, update: NotificationUpdate): Promise<Notification> {
    const response = await axios.put(`${this.baseURL}/${id}`, update);
    return response.data;
  }

  async deleteNotification(id: number): Promise<void> {
    await axios.delete(`${this.baseURL}/${id}`);
  }

  async markAsRead(id: number): Promise<void> {
    await axios.post(`${this.baseURL}/${id}/read`);
  }

  async sendNotification(id: number): Promise<void> {
    await axios.post(`${this.baseURL}/${id}/send`);
  }

  async getNotificationStats(): Promise<NotificationStats> {
    const response = await axios.get(`${this.baseURL}/stats`);
    return response.data;
  }

  async getAdminNotificationStats(): Promise<NotificationStats> {
    const response = await axios.get(`${this.baseURL}/admin/stats`);
    return response.data;
  }

  // 通知模板相关方法
  async createTemplate(template: Omit<NotificationTemplate, 'id' | 'created_at' | 'updated_at'>): Promise<NotificationTemplate> {
    const response = await axios.post(`${this.baseURL}/templates/`, template);
    return response.data;
  }

  async getTemplates(params?: {
    notification_type?: string;
    is_active?: boolean;
  }): Promise<NotificationTemplate[]> {
    const queryParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }

    const response = await axios.get(`${this.baseURL}/templates/?${queryParams.toString()}`);
    return response.data;
  }

  async getTemplate(id: number): Promise<NotificationTemplate> {
    const response = await axios.get(`${this.baseURL}/templates/${id}`);
    return response.data;
  }

  async updateTemplate(id: number, update: Partial<NotificationTemplate>): Promise<NotificationTemplate> {
    const response = await axios.put(`${this.baseURL}/templates/${id}`, update);
    return response.data;
  }

  async deleteTemplate(id: number): Promise<void> {
    await axios.delete(`${this.baseURL}/templates/${id}`);
  }

  // 通知规则相关方法
  async createRule(rule: Omit<NotificationRule, 'id' | 'created_at' | 'updated_at'>): Promise<NotificationRule> {
    const response = await axios.post(`${this.baseURL}/rules/`, rule);
    return response.data;
  }

  async getRules(params?: {
    trigger_event?: string;
    is_active?: boolean;
  }): Promise<NotificationRule[]> {
    const queryParams = new URLSearchParams();
    
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          queryParams.append(key, value.toString());
        }
      });
    }

    const response = await axios.get(`${this.baseURL}/rules/?${queryParams.toString()}`);
    return response.data;
  }

  async updateRule(id: number, update: Partial<NotificationRule>): Promise<NotificationRule> {
    const response = await axios.put(`${this.baseURL}/rules/${id}`, update);
    return response.data;
  }

  async deleteRule(id: number): Promise<void> {
    await axios.delete(`${this.baseURL}/rules/${id}`);
  }

  // 管理员功能
  async retryFailedNotifications(): Promise<void> {
    await axios.post(`${this.baseURL}/admin/retry-failed`);
  }

  async processScheduledNotifications(): Promise<void> {
    await axios.post(`${this.baseURL}/admin/process-scheduled`);
  }

  async triggerNotificationEvent(event: string, eventData: Record<string, any>): Promise<void> {
    await axios.post(`${this.baseURL}/admin/trigger-event`, null, {
      params: { event },
      data: eventData
    });
  }

  // 实时通知相关方法
  async subscribeToNotifications(userId: number, callback: (notification: Notification) => void): Promise<EventSource | null> {
    if (typeof EventSource !== 'undefined') {
      const eventSource = new EventSource(`${this.baseURL}/stream/${userId}`);
      
      eventSource.onmessage = (event) => {
        try {
          const notification = JSON.parse(event.data);
          callback(notification);
        } catch (error) {
          console.error('Error parsing notification:', error);
        }
      };

      eventSource.onerror = (error) => {
        console.error('EventSource error:', error);
      };

      return eventSource;
    }
    return null;
  }

  // 批量操作
  async markMultipleAsRead(ids: number[]): Promise<void> {
    await Promise.all(ids.map(id => this.markAsRead(id)));
  }

  async deleteMultiple(ids: number[]): Promise<void> {
    await Promise.all(ids.map(id => this.deleteNotification(id)));
  }

  // 导出通知数据
  async exportNotifications(query?: NotificationQuery): Promise<Blob> {
    const params = new URLSearchParams();
    
    if (query) {
      Object.entries(query).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
    }

    const response = await axios.get(`${this.baseURL}/export?${params.toString()}`, {
      responseType: 'blob'
    });
    
    return response.data;
  }
}

export const notificationService = new NotificationService();
export default notificationService;