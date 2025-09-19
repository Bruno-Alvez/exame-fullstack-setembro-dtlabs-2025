import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatRelativeTime(date: string | Date): string {
  const now = new Date();
  const d = new Date(date);
  const diffInSeconds = Math.floor((now.getTime() - d.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'Just now';
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} hour${hours > 1 ? 's' : ''} ago`;
  } else {
    const days = Math.floor(diffInSeconds / 86400);
    return `${days} day${days > 1 ? 's' : ''} ago`;
  }
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatTemperature(value: number): string {
  return `${value.toFixed(1)}°C`;
}

export function formatLatency(value: number): string {
  return `${value.toFixed(0)}ms`;
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'healthy':
      return 'text-success-600 bg-success-100 border-success-200';
    case 'warning':
      return 'text-warning-600 bg-warning-100 border-warning-200';
    case 'critical':
      return 'text-danger-600 bg-danger-100 border-danger-200';
    case 'offline':
      return 'text-secondary-600 bg-secondary-100 border-secondary-200';
    default:
      return 'text-secondary-600 bg-secondary-100 border-secondary-200';
  }
}

export function getHealthScoreColor(score: number): string {
  if (score >= 80) return 'text-success-600';
  if (score >= 60) return 'text-warning-600';
  return 'text-danger-600';
}

export function getHealthScoreBgColor(score: number): string {
  if (score >= 80) return 'bg-success-100';
  if (score >= 60) return 'bg-warning-100';
  return 'bg-danger-100';
}

export function validateSerialNumber(sn: string): boolean {
  return /^\d{12}$/.test(sn);
}

export function formatSerialNumber(sn: string): string {
  return sn.replace(/(\d{4})(\d{4})(\d{4})/, '$1-$2-$3');
}

export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: number;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
}

export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

export function generateTimeRanges() {
  const now = new Date();
  
  return {
    lastHour: {
      start: new Date(now.getTime() - 60 * 60 * 1000),
      end: now,
      label: 'Last Hour',
    },
    last24Hours: {
      start: new Date(now.getTime() - 24 * 60 * 60 * 1000),
      end: now,
      label: 'Last 24 Hours',
    },
    last7Days: {
      start: new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000),
      end: now,
      label: 'Last 7 Days',
    },
    last30Days: {
      start: new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000),
      end: now,
      label: 'Last 30 Days',
    },
  };
}

export function calculateTrend(current: number, previous: number): 'up' | 'down' | 'stable' {
  const diff = current - previous;
  const threshold = 0.1; // 10% threshold
  
  if (Math.abs(diff) < threshold) return 'stable';
  return diff > 0 ? 'up' : 'down';
}

export function exportToCSV(data: any[], filename: string) {
  if (!data.length) return;
  
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        return typeof value === 'string' && value.includes(',') 
          ? `"${value}"` 
          : value;
      }).join(',')
    )
  ].join('\n');
  
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', `${filename}.csv`);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

export function exportToJSON(data: any[], filename: string) {
  const jsonContent = JSON.stringify(data, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', `${filename}.json`);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
