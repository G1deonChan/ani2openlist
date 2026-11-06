const $ = id => document.getElementById(id);
const api = {
    pending: new Map(),
    async request(url, method, data) {
        const key = method + url;
        if (this.pending.has(key)) return this.pending.get(key);
        const promise = (async () => {
            const controller = new AbortController();
            const timer = setTimeout(() => controller.abort(), 15000);
            try {
                const response = await fetch(url, {
                    method,
                    signal: controller.signal,
                    headers: data === undefined ? {} : {
                        'Content-Type': 'application/json'
                    },
                    body: data === undefined ? undefined : JSON.stringify(data)
                });
                const body = await response.json();
                if (!response.ok) {
                    const error = new Error(body.error || '请求失败');
                    error.response = {
                        data: body,
                        status: response.status
                    };
                    throw error;
                }
                return {
                    data: body
                };
            } finally {
                clearTimeout(timer);
            }
        })();
        this.pending.set(key, promise);
        try {
            return await promise;
        } finally {
            this.pending.delete(key);
        }
    },
    get(url) {
        return this.request(url, 'GET');
    },
    post(url, data) {
        return this.request(url, 'POST', data);
    }
};

function node(tag, text, className) {
    const el = document.createElement(tag);
    if (text !== undefined) el.textContent = String(text ?? '');
    if (className) el.className = className;
    return el;
}

function showAlert(message, type = 'info') {
    const container = $('alert-container');
    if (!container) return;
    const alert = node('div', undefined, 'alert alert-' + type);
    alert.setAttribute('role', type === 'error' ? 'alert' : 'status');
    alert.append(node('p', message));
    const close = node('button', '×');
    close.type = 'button';
    close.setAttribute('aria-label', '关闭提示');
    close.onclick = () => alert.remove();
    alert.append(close);
    container.replaceChildren(alert);
}

function errorMessage(error, fallback) {
    return error.response?.data?.error || (error.name === 'AbortError' ? '请求超时，请稍后重试' : fallback);
}
async function busy(button, action) {
    if (button.disabled) return;
    button.disabled = true;
    button.setAttribute('aria-busy', 'true');
    try {
        return await action();
    } finally {
        button.disabled = false;
        button.removeAttribute('aria-busy');
    }
}

function confirmAction(message, title = '确认操作') {
    const dialog = $('confirm-dialog');
    if (dialog.open) return Promise.resolve(false);
    $('confirm-title').textContent = title;
    $('confirm-message').textContent = message;
    dialog.returnValue = '';
    return new Promise(resolve => {
        dialog.addEventListener('close', () => resolve(dialog.returnValue === 'confirm'), {
            once: true
        });
        dialog.showModal();
    });
}

function renderLogs(container, logs, emptyMessage = '暂无日志，运行任务后会在这里显示记录。') {
    const fragment = document.createDocumentFragment();
    const labels = {
        success: '成功',
        info: '信息',
        warning: '警告',
        error: '错误'
    };
    for (const log of logs) {
        const row = node('div', undefined, 'log-row');
        const level = Object.hasOwn(labels, log.level) ? log.level : 'info';
        row.append(node('time', log.time), node('span', labels[log.level] || log.level, 'badge ' + level),
            node('p', log.message, 'log-message'));
        fragment.append(row);
    }
    if (!logs.length) fragment.append(node('p', emptyMessage, 'empty'));
    container.replaceChildren(fragment);
}

function refreshState(failed = false) {
    const el = $('refresh-state');
    if (el) {
        el.classList.toggle('failed', failed);
        el.textContent = failed ? '刷新失败，保留上次数据；将自动重试' : '已更新 · ' + new Date().toLocaleTimeString('zh-CN');
    }
}
const themeSelect = $('theme'),
    systemTheme = matchMedia('(prefers-color-scheme: dark)');
try {
    const saved = localStorage.getItem('theme');
    if (['light', 'dark', 'system'].includes(saved)) themeSelect.value = saved;
} catch (e) {}

function applyTheme() {
    document.documentElement.dataset.theme = themeSelect.value === 'system' ? (systemTheme.matches ? 'dark' :
        'light') : themeSelect.value;
    try {
        localStorage.setItem('theme', themeSelect.value);
    } catch (e) {}
}
themeSelect.addEventListener('change', applyTheme);
systemTheme.addEventListener('change', applyTheme);

function setMenu(open) {
    document.body.classList.toggle('nav-open', open);
    $('menu-toggle').setAttribute('aria-expanded', String(open));
    $('nav-backdrop').hidden = !open;
    $('sidebar').inert = !open && innerWidth < 768;
    if (open) $('sidebar').querySelector('a').focus();
}
$('menu-toggle').onclick = () => setMenu(!document.body.classList.contains('nav-open'));
$('nav-backdrop').onclick = () => {
    setMenu(false);
    $('menu-toggle').focus();
};
document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && document.body.classList.contains('nav-open')) {
        setMenu(false);
        $('menu-toggle').focus();
    }
    if (e.key === 'Tab' && document.body.classList.contains('nav-open')) {
        const items = [...$('sidebar').querySelectorAll('a,select')];
        if (e.shiftKey && document.activeElement === items[0]) {
            e.preventDefault();
            items.at(-1).focus();
        } else if (!e.shiftKey && document.activeElement === items.at(-1)) {
            e.preventDefault();
            items[0].focus();
        }
    }
});
addEventListener('resize', () => {
    if (innerWidth >= 768) setMenu(false);
    else $('sidebar').inert = !document.body.classList.contains('nav-open');
});
setMenu(false);
document.querySelectorAll('input[type=password]').forEach(input => {
    const wrapper = node('div', undefined, 'secret-field');
    input.before(wrapper);
    wrapper.append(input);
    const button = node('button', '显示', 'btn');
    button.type = 'button';
    button.setAttribute('aria-label', '显示' + (input.id.includes('token') ? ' Token' : '密码'));
    button.setAttribute('aria-pressed', 'false');
    button.onclick = () => {
        const visible = input.type === 'password';
        input.type = visible ? 'text' : 'password';
        button.textContent = visible ? '隐藏' : '显示';
        button.setAttribute('aria-pressed', String(visible));
        button.setAttribute('aria-label', (visible ? '隐藏' : '显示') + (input.id.includes('token') ?
            ' Token' : '密码'));
    };
    wrapper.append(button);
});
