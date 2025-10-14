"""
Ani2Openlist Web UI
基于 Flask 的 Web 管理界面
"""
import os
import sys
import asyncio
import threading
import yaml
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ani2openlist import Ani2Openlist, load_config, Config
from ani2openlist.core.logger import logger
from ani2openlist.utils.http import RequestUtils

app = Flask(__name__)
app.config['SECRET_KEY'] = 'ani2openlist-secret-key-change-in-production'

# 全局变量
scheduler = BackgroundScheduler()
scheduler.start()

# 任务状态
task_status = {
    'running': False,
    'last_run': None,
    'last_result': None,
    'logs': []
}

# 配置文件路径
CONFIG_PATH = Path(__file__).parent.parent / 'config.yaml'
SCHEDULE_CONFIG_PATH = Path(__file__).parent / 'schedule.yaml'


def load_schedule_config():
    """加载定时任务配置"""
    if SCHEDULE_CONFIG_PATH.exists():
        with open(SCHEDULE_CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {'enabled': False, 'type': 'daily', 'time': '10:00'}


def save_schedule_config(config):
    """保存定时任务配置"""
    with open(SCHEDULE_CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True)


def add_log(message, level='info'):
    """添加日志"""
    log_entry = {
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'level': level,
        'message': message
    }
    task_status['logs'].insert(0, log_entry)
    # 只保留最近100条日志
    task_status['logs'] = task_status['logs'][:100]


async def run_ani2openlist_async():
    """异步运行 ani2openlist"""
    ani = None
    try:
        add_log('开始执行任务...')
        config = load_config(str(CONFIG_PATH))
        ani = Ani2Openlist(config=config)
        await ani.run()
        add_log('任务执行完成', 'success')
        return {'success': True, 'message': '任务执行成功'}
    except Exception as e:
        error_msg = f'任务执行失败: {str(e)}'
        add_log(error_msg, 'error')
        return {'success': False, 'message': error_msg}
    finally:
        # 清理所有 HTTP 客户端资源并清除缓存
        # 下次任务时会自动创建新的客户端
        try:
            await RequestUtils.close_all_async_clients()
        except Exception as e:
            logger.debug(f'清理 HTTP 客户端失败: {e}')


def run_ani2openlist():
    """运行 ani2openlist 任务"""
    if task_status['running']:
        add_log('任务已在运行中，跳过', 'warning')
        return
    
    task_status['running'] = True
    task_status['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def _run_in_thread():
        """在独立线程中运行异步任务"""
        try:
            # 方案：完全不依赖 get_event_loop()，手动创建和管理循环
            # 1. 创建新的事件循环策略
            if sys.platform == 'win32':
                policy = asyncio.WindowsSelectorEventLoopPolicy()
            else:
                policy = asyncio.DefaultEventLoopPolicy()
            
            # 2. 创建全新的事件循环
            loop = policy.new_event_loop()
            
            # 3. 设置为当前线程的事件循环
            asyncio.set_event_loop(loop)
            
            try:
                # 4. 运行异步任务
                result = loop.run_until_complete(run_ani2openlist_async())
                task_status['last_result'] = result
            finally:
                # 5. 清理：关闭所有异步生成器
                try:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                except Exception:
                    pass
                
                # 6. 清理：关闭所有异步上下文管理器
                try:
                    loop.run_until_complete(loop.shutdown_default_executor())
                except Exception:
                    pass
                
                # 7. 关闭循环
                loop.close()
                
                # 8. 清除线程的事件循环引用
                asyncio.set_event_loop(None)
                
        except Exception as e:
            error_msg = f'任务执行失败: {str(e)}'
            add_log(error_msg, 'error')
            task_status['last_result'] = {'success': False, 'message': error_msg}
        finally:
            task_status['running'] = False
    
    # 在新线程中运行，避免干扰主事件循环
    thread = threading.Thread(target=_run_in_thread, daemon=True)
    thread.start()


def setup_scheduler():
    """设置定时任务"""
    schedule_config = load_schedule_config()
    
    # 清除现有任务
    scheduler.remove_all_jobs()
    
    if not schedule_config.get('enabled', False):
        add_log('定时任务未启用')
        return
    
    schedule_type = schedule_config.get('type', 'daily')
    
    if schedule_type == 'daily':
        # 每天指定时间运行
        time_str = schedule_config.get('time', '10:00')
        hour, minute = map(int, time_str.split(':'))
        scheduler.add_job(
            run_ani2openlist,
            CronTrigger(hour=hour, minute=minute),
            id='ani2openlist_daily',
            name='每日更新',
            replace_existing=True
        )
        add_log(f'已设置每日定时任务: {time_str}')
    
    elif schedule_type == 'interval':
        # 按间隔运行（小时）
        hours = schedule_config.get('hours', 6)
        scheduler.add_job(
            run_ani2openlist,
            'interval',
            hours=hours,
            id='ani2openlist_interval',
            name=f'每{hours}小时更新',
            replace_existing=True
        )
        add_log(f'已设置间隔定时任务: 每{hours}小时')
    
    elif schedule_type == 'cron':
        # 自定义 Cron 表达式
        cron_expr = schedule_config.get('cron', '0 10 * * *')
        # 解析 cron 表达式
        parts = cron_expr.split()
        if len(parts) == 5:
            minute, hour, day, month, day_of_week = parts
            scheduler.add_job(
                run_ani2openlist,
                CronTrigger(
                    minute=minute,
                    hour=hour,
                    day=day,
                    month=month,
                    day_of_week=day_of_week
                ),
                id='ani2openlist_cron',
                name='自定义定时',
                replace_existing=True
            )
            add_log(f'已设置自定义定时任务: {cron_expr}')


@app.route('/health')
def health_check():
    """健康检查端点 - 用于 Docker 容器健康检查"""
    try:
        # 检查配置文件是否存在
        config_exists = CONFIG_PATH.exists()
        
        # 检查调度器状态
        scheduler_running = scheduler.running
        
        # 返回健康状态
        status = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'config_exists': config_exists,
            'scheduler_running': scheduler_running,
            'task_running': task_status['running']
        }
        
        return jsonify(status), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/config')
def config_page():
    """配置页面"""
    config_data = {}
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f) or {}
        except Exception as e:
            config_data = {'error': str(e)}
    
    return render_template('config.html', config=config_data)


@app.route('/api/config', methods=['GET'])
def get_config():
    """获取配置"""
    if not CONFIG_PATH.exists():
        return jsonify({'error': '配置文件不存在'}), 404
    
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
        return jsonify(config_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/config', methods=['POST'])
def save_config():
    """保存配置"""
    try:
        config_data = request.json
        
        # 验证必需字段
        if 'openlist' not in config_data:
            return jsonify({'error': '缺少 openlist 配置'}), 400
        
        # 保存配置
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
        
        add_log('配置已更新', 'success')
        return jsonify({'success': True, 'message': '配置保存成功'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/schedule')
def schedule_page():
    """定时任务页面"""
    schedule_config = load_schedule_config()
    
    # 获取当前任务列表
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'N/A'
        })
    
    return render_template('schedule.html', config=schedule_config, jobs=jobs)


@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """获取定时任务配置"""
    config = load_schedule_config()
    
    # 添加任务列表
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else 'N/A'
        })
    
    config['jobs'] = jobs
    return jsonify(config)


@app.route('/api/schedule', methods=['POST'])
def save_schedule():
    """保存定时任务配置"""
    try:
        config = request.json
        save_schedule_config(config)
        setup_scheduler()
        return jsonify({'success': True, 'message': '定时任务配置已更新'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/run', methods=['POST'])
def run_task():
    """手动运行任务"""
    if task_status['running']:
        return jsonify({'error': '任务正在运行中'}), 400
    
    # 在后台线程中运行
    thread = threading.Thread(target=run_ani2openlist)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': '任务已启动'})


@app.route('/api/status', methods=['GET'])
def get_status():
    """获取任务状态"""
    return jsonify(task_status)


@app.route('/logs')
def logs_page():
    """日志页面"""
    return render_template('logs.html', logs=task_status['logs'])


@app.route('/api/logs', methods=['GET'])
def get_logs():
    """获取日志"""
    return jsonify({'logs': task_status['logs']})


@app.route('/api/logs/clear', methods=['POST'])
def clear_logs():
    """清除日志"""
    task_status['logs'] = []
    add_log('日志已清除')
    return jsonify({'success': True, 'message': '日志已清除'})


if __name__ == '__main__':
    # 初始化定时任务
    setup_scheduler()
    add_log('Web UI 已启动', 'success')
    
    # 启动 Flask 应用
    print('=' * 60)
    print('Ani2Openlist Web UI 已启动')
    print('访问地址: http://localhost:5000')
    print('=' * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
