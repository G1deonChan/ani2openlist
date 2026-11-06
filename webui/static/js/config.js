let loading = false,
    saving = false,
    dirty = false;
// RSS 模式切换
document.getElementById('ani_rss_update').addEventListener('change', function() {
    const manualConfig = document.getElementById('manual-config');
    manualConfig.style.display = this.checked ? 'none' : 'block';
});

async function loadConfig(confirmReload = false) {
    if (loading || saving) return;
    if (confirmReload && dirty && !await confirmAction('重新加载会丢弃尚未保存的修改。', '重新加载配置')) return;
    loading = true;
    const submit = document.querySelector('[type=submit]');
    submit.disabled = true;
    try {
        const response = await api.get('/api/config');
        const config = response.data;

        if (config.error) {
            showAlert('配置文件不存在或格式错误', 'error');
            return;
        }

        // 填充 Openlist 配置
        if (config.openlist) {
            document.getElementById('openlist_url').value = config.openlist.url || '';
            document.getElementById('openlist_username').value = config.openlist.username || '';
            document.getElementById('openlist_password').value = config.openlist.password || '';
            document.getElementById('openlist_token').value = config.openlist.token || '';
            document.getElementById('openlist_target_dir').value = config.openlist.target_dir || '/Anime';
        }

        // 填充 ANI 配置
        if (config.ani) {
            const rssUpdate = config.ani.rss_update !== false;
            document.getElementById('ani_rss_update').checked = rssUpdate;
            document.getElementById('manual-config').style.display = rssUpdate ? 'none' : 'block';

            document.getElementById('ani_year').value = config.ani.year || '';
            document.getElementById('ani_month').value = config.ani.month || '';
            document.getElementById('ani_key_word').value = config.ani.key_word || '';
            document.getElementById('ani_src_domain').value = config.ani.src_domain ||
                'aniopen.an-i.workers.dev';
            document.getElementById('ani_rss_domain').value = config.ani.rss_domain || 'api.ani.rip';
            document.getElementById('ani_flaresolverr_url').value = config.ani.flaresolverr_url || '';
            document.getElementById('ani_flaresolverr_timeout').value = config.ani.flaresolverr_timeout ??
                60000;
            document.getElementById('ani_resource_domain').value = config.ani.resource_domain || '';
        }

        document.getElementById('http_timeout').value = config.http?.timeout ?? 30;
        document.getElementById('openlist_update_timeout').value = config.openlist?.update_timeout ?? 120;

        // 填充日志配置
        if (config.logging) {
            document.getElementById('logging_level').value = config.logging.level || 'INFO';
            document.getElementById('logging_format').value = config.logging.format ||
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s';
        }

        dirty = false;
        $('form-state').textContent = '配置已加载';
    } catch (error) {
        console.error('加载配置失败:', error);
        showAlert(error.response?.status === 404 ? '尚无配置文件，请填写连接信息并保存。' : errorMessage(error,
            '加载配置失败，请重试'), 'error');
        $('form-state').textContent = '配置未加载';
    } finally {
        loading = false;
        submit.disabled = false;
    }
}

document.getElementById('config-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    if (saving || loading) return;
    if (!this.checkValidity()) {
        this.reportValidity();
        return;
    }
    const httpTimeout = Number(document.getElementById('http_timeout').value);
    const updateTimeout = Number(document.getElementById('openlist_update_timeout').value);
    if (!Number.isFinite(updateTimeout) || updateTimeout <= 0) {
        showAlert('存储写回等待时间必须是大于 0 的有限秒数', 'error');
        return;
    }
    if (!Number.isFinite(httpTimeout) || httpTimeout <= 0) {
        showAlert('HTTP 请求超时必须是大于 0 的有限秒数', 'error');
        return;
    }

    // 构建配置对象
    const config = {
        openlist: {
            url: document.getElementById('openlist_url').value,
            username: document.getElementById('openlist_username').value,
            password: document.getElementById('openlist_password').value,
            token: document.getElementById('openlist_token').value,
            target_dir: document.getElementById('openlist_target_dir').value,
            update_timeout: updateTimeout
        },
        ani: {
            rss_update: document.getElementById('ani_rss_update').checked,
            src_domain: document.getElementById('ani_src_domain').value,
            rss_domain: document.getElementById('ani_rss_domain').value,
            flaresolverr_url: document.getElementById('ani_flaresolverr_url').value,
            flaresolverr_timeout: Number(document.getElementById('ani_flaresolverr_timeout')
                .value),
            resource_domain: document.getElementById('ani_resource_domain').value
        },
        http: {
            timeout: httpTimeout
        },
        logging: {
            level: document.getElementById('logging_level').value,
            format: document.getElementById('logging_format').value
        }
    };

    // 如果不是 RSS 模式，添加手动配置
    if (!config.ani.rss_update) {
        const year = document.getElementById('ani_year').value;
        const month = document.getElementById('ani_month').value;
        const keyword = document.getElementById('ani_key_word').value;

        if (year) config.ani.year = parseInt(year);
        if (month) config.ani.month = parseInt(month);
        if (keyword) config.ani.key_word = keyword;
    }

    saving = true;
    const button = this.querySelector('[type=submit]');
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    try {
        const response = await api.post('/api/config', config);
        showAlert(response.data.message, 'success');
        dirty = false;
        $('form-state').textContent = '所有修改已保存';
    } catch (error) {
        showAlert(error.response?.data?.error || '保存配置失败', 'error');
    } finally {
        saving = false;
        button.disabled = false;
        button.removeAttribute('aria-busy');
    }
});

// 页面加载时加载配置
document.addEventListener('DOMContentLoaded', loadConfig);

$('config-form').addEventListener('input', () => {
    dirty = true;
    $('form-state').textContent = '有未保存的修改';
});
addEventListener('beforeunload', e => {
    if (dirty) {
        e.preventDefault();
        e.returnValue = '';
    }
});
