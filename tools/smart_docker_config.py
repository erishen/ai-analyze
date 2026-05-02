#!/usr/bin/env python3
"""
智能 Docker 配置生成器
基于代码复杂度分析自动调整资源分配
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, Optional


@dataclass
class ResourceProfile:
    """资源配置文件"""
    name: str
    cpu_limit: str
    memory_limit: str
    memory_request: str
    cpu_request: str
    description: str


class SmartDockerConfig:
    """智能 Docker 配置生成器"""

    # 资源配置预设
    RESOURCE_PROFILES = {
        'minimal': ResourceProfile(
            name='minimal',
            cpu_limit='0.5',
            memory_limit='256m',
            memory_request='128m',
            cpu_request='0.1',
            description='极小型项目 (简单脚本、静态网站)'
        ),
        'small': ResourceProfile(
            name='small',
            cpu_limit='1',
            memory_limit='512m',
            memory_request='256m',
            cpu_request='0.25',
            description='小型项目 (低复杂度)'
        ),
        'medium': ResourceProfile(
            name='medium',
            cpu_limit='2',
            memory_limit='1g',
            memory_request='512m',
            cpu_request='0.5',
            description='中型项目 (中等复杂度)'
        ),
        'large': ResourceProfile(
            name='large',
            cpu_limit='4',
            memory_limit='2g',
            memory_request='1g',
            cpu_request='1',
            description='大型项目 (高复杂度)'
        ),
        'xlarge': ResourceProfile(
            name='xlarge',
            cpu_limit='8',
            memory_limit='4g',
            memory_request='2g',
            cpu_request='2',
            description='超大型项目 (极高复杂度)'
        ),
    }

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)

    def analyze_complexity(self, analysis_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        分析代码复杂度

        Args:
            analysis_data: 来自 Serena/AST 分析的数据

        Returns:
            复杂度分析结果
        """
        metrics = {
            'file_count': 0,
            'total_complexity': 0.0,
            'avg_complexity': 0.0,
            'max_complexity': 0.0,
            'code_smells': 0,
            'quality_score': 100.0,
            'language_distribution': {},
            'complexity_level': 'unknown'
        }

        if not analysis_data:
            return metrics

        # 从分析数据提取指标
        files = analysis_data.get('files', [])
        metrics['file_count'] = len(files)

        if files:
            complexities = []

            for file_data in files:
                # 提取语言信息
                language = file_data.get('language', 'unknown')
                metrics['language_distribution'][language] = \
                    metrics['language_distribution'].get(language, 0) + 1

                # 提取复杂度
                if file_data.get('overall_complexity'):
                    cc = file_data['overall_complexity'].get('cyclomatic_complexity', 0)
                    complexities.append(cc)
                    metrics['total_complexity'] += cc
                    metrics['max_complexity'] = max(metrics['max_complexity'], cc)

                # 提取代码坏味道
                metrics['code_smells'] += len(file_data.get('code_smells', []))

            # 计算平均复杂度
            if complexities:
                metrics['avg_complexity'] = metrics['total_complexity'] / len(complexities)

            # 提取质量分数
            summary = analysis_data.get('summary', {})
            metrics['quality_score'] = summary.get('quality_score', 100.0)

        # 确定复杂度级别
        metrics['complexity_level'] = self._classify_complexity(metrics)

        return metrics

    def _classify_complexity(self, metrics: Dict[str, Any]) -> str:
        """
        根据指标分类复杂度级别

        Returns:
            'minimal', 'small', 'medium', 'large', 'xlarge'
        """
        file_count = metrics['file_count']
        avg_complexity = metrics['avg_complexity']
        max_complexity = metrics['max_complexity']
        code_smells = metrics['code_smells']
        quality_score = metrics['quality_score']

        # 计算复杂度分数 (0-100)
        complexity_score = 0

        # 文件数量评分 (0-25)
        if file_count < 10:
            complexity_score += 5
        elif file_count < 50:
            complexity_score += 10
        elif file_count < 100:
            complexity_score += 15
        elif file_count < 500:
            complexity_score += 20
        else:
            complexity_score += 25

        # 平均复杂度评分 (0-25)
        if avg_complexity < 5:
            complexity_score += 5
        elif avg_complexity < 10:
            complexity_score += 10
        elif avg_complexity < 20:
            complexity_score += 15
        elif avg_complexity < 50:
            complexity_score += 20
        else:
            complexity_score += 25

        # 最大复杂度评分 (0-25)
        if max_complexity < 10:
            complexity_score += 5
        elif max_complexity < 30:
            complexity_score += 10
        elif max_complexity < 100:
            complexity_score += 15
        elif max_complexity < 300:
            complexity_score += 20
        else:
            complexity_score += 25

        # 代码坏味道评分 (0-25)
        if code_smells == 0:
            complexity_score += 25
        elif code_smells < 5:
            complexity_score += 20
        elif code_smells < 20:
            complexity_score += 15
        elif code_smells < 50:
            complexity_score += 10
        else:
            complexity_score += 5

        # 根据总分分类
        if complexity_score < 20:
            return 'minimal'
        elif complexity_score < 40:
            return 'small'
        elif complexity_score < 60:
            return 'medium'
        elif complexity_score < 80:
            return 'large'
        else:
            return 'xlarge'

    def get_resource_profile(self, analysis_data: Optional[Dict[str, Any]] = None) -> ResourceProfile:
        """
        根据分析数据获取推荐的资源配置

        Args:
            analysis_data: 来自 Serena/AST 分析的数据

        Returns:
            推荐的资源配置
        """
        metrics = self.analyze_complexity(analysis_data)
        complexity_level = metrics['complexity_level']

        return self.RESOURCE_PROFILES.get(complexity_level, self.RESOURCE_PROFILES['medium'])

    def generate_docker_compose(
        self,
        service_name: str,
        image: str,
        port: int,
        analysis_data: Optional[Dict[str, Any]] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> str:
        """
        生成优化的 docker-compose.yml

        Args:
            service_name: 服务名称
            image: Docker 镜像名称
            port: 服务端口
            analysis_data: 分析数据
            env_vars: 环境变量

        Returns:
            docker-compose.yml 内容
        """
        profile = self.get_resource_profile(analysis_data)
        metrics = self.analyze_complexity(analysis_data)

        env_section = ''
        if env_vars:
            env_lines = [f'      {k}: "{v}"' for k, v in env_vars.items()]
            env_section = '    environment:\n' + '\n'.join(env_lines) + '\n'

        compose_content = '''version: '3.8'

services:
  {service_name}:
    image: {image}
    container_name: {service_name}
    ports:
      - "{port}:{port}"
{env_section}    # 资源限制 - 基于代码复杂度自动调整
    # 复杂度级别: {profile.name} ({metrics['complexity_level']})
    # 文件数: {metrics['file_count']}, 平均复杂度: {metrics['avg_complexity']:.1f}
    deploy:
      resources:
        limits:
          cpus: '{profile.cpu_limit}'
          memory: {profile.memory_limit}
        reservations:
          cpus: '{profile.cpu_request}'
          memory: {profile.memory_request}

    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-", "http://localhost:{port}/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # 重启策略
    restart: unless-stopped

    # 日志配置
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

# 网络配置
networks:
  default:
    name: {service_name}-network
    driver: bridge
'''
        return compose_content

    def generate_kubernetes_deployment(
        self,
        app_name: str,
        image: str,
        port: int,
        replicas: int = 1,
        analysis_data: Optional[Dict[str, Any]] = None,
        env_vars: Optional[Dict[str, str]] = None
    ) -> str:
        """
        生成优化的 Kubernetes Deployment

        Args:
            app_name: 应用名称
            image: Docker 镜像
            port: 服务端口
            replicas: 副本数
            analysis_data: 分析数据
            env_vars: 环境变量

        Returns:
            Kubernetes Deployment YAML
        """
        profile = self.get_resource_profile(analysis_data)
        metrics = self.analyze_complexity(analysis_data)

        env_section = ''
        if env_vars:
            env_lines = [f'        - name: {k}\n          value: "{v}"' for k, v in env_vars.items()]
            env_section = '          env:\n' + '\n'.join(env_lines) + '\n'

        deployment = '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_name}
  labels:
    app: {app_name}
    complexity: {metrics['complexity_level']}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {app_name}
  template:
    metadata:
      labels:
        app: {app_name}
    spec:
      containers:
      - name: {app_name}
        image: {image}
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: {port}
          name: http
{env_section}        # 资源限制 - 基于代码复杂度自动调整
        # 复杂度级别: {profile.name}
        # 文件数: {metrics['file_count']}, 平均复杂度: {metrics['avg_complexity']:.1f}
        resources:
          limits:
            cpu: {profile.cpu_limit}
            memory: {profile.memory_limit}
          requests:
            cpu: {profile.cpu_request}
            memory: {profile.memory_request}

        # 健康检查
        livenessProbe:
          httpGet:
            path: /
            port: {port}
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /
            port: {port}
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3

        # 安全上下文
        securityContext:
          runAsNonRoot: true
          readOnlyRootFilesystem: false
          allowPrivilegeEscalation: false
          capabilities:
            drop:
              - ALL

---
apiVersion: v1
kind: Service
metadata:
  name: {app_name}-service
  labels:
    app: {app_name}
spec:
  type: ClusterIP
  ports:
  - port: {port}
    targetPort: {port}
    protocol: TCP
    name: http
  selector:
    app: {app_name}
'''
        return deployment

    def generate_resource_report(self, analysis_data: Optional[Dict[str, Any]] = None) -> str:
        """
        生成资源配置报告

        Args:
            analysis_data: 分析数据

        Returns:
            格式化的报告文本
        """
        metrics = self.analyze_complexity(analysis_data)
        profile = self.get_resource_profile(analysis_data)

        report = '''
╔════════════════════════════════════════════════════════════════╗
║           智能 Docker 资源配置分析报告                          ║
╚════════════════════════════════════════════════════════════════╝

📊 代码复杂度指标
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  文件数量:           {metrics['file_count']} 个
  总复杂度:           {metrics['total_complexity']:.1f}
  平均复杂度:         {metrics['avg_complexity']:.1f}
  最大复杂度:         {metrics['max_complexity']:.1f}
  代码坏味道:         {metrics['code_smells']} 个
  质量分数:           {metrics['quality_score']:.1f}/100

📈 语言分布
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
'''
        for lang, count in sorted(metrics['language_distribution'].items(), key=lambda x: x[1], reverse=True):
            report += f'  {lang:15} {count:3} 个文件\n'

        report += '''
🎯 推荐资源配置
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  配置级别:           {profile.name.upper()}
  描述:               {profile.description}

  CPU 限制:           {profile.cpu_limit} 核
  CPU 请求:           {profile.cpu_request} 核
  内存限制:           {profile.memory_limit}
  内存请求:           {profile.memory_request}

💡 优化建议
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
'''

        # 根据指标生成建议
        if metrics['avg_complexity'] > 20:
            report += '  ⚠️  平均复杂度较高，建议进行代码重构\n'

        if metrics['code_smells'] > 10:
            report += '  ⚠️  代码坏味道较多，建议进行代码审查\n'

        if metrics['quality_score'] < 70:
            report += '  ⚠️  代码质量分数较低，建议改进\n'

        if metrics['file_count'] > 100:
            report += '  💡 文件数量较多，考虑增加副本数以提高可用性\n'

        if metrics['complexity_level'] in ['large', 'xlarge']:
            report += '  💡 项目复杂度较高，建议使用多副本部署\n'
            report += '  💡 建议启用自动扩展 (HPA)\n'

        report += '\n'
        return report
