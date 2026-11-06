let logs = [],
    refreshing = false,
    clearing = false;

function filterLogs() {
    const keyword = $('log-search').value.toLocaleLowerCase(),
        level = $('log-level').value;
    const filtered = logs.filter(log => (level === 'all' || log.level === level) && String(log.message)
        .toLocaleLowerCase().includes(keyword));
    renderLogs($('logs-container'), filtered, logs.length ? '没有符合条件的日志。' : '暂无日志，运行任务后会在这里显示记录。');
    $('log-count').textContent = `匹配 ${filtered.length} / ${logs.length} 条 · 仅筛选服务端最近 100 条记录`;
}
async function refreshLogs() {
    if (refreshing) return;
    refreshing = true;
    try {
        const {
            data
        } = await api.get('/api/logs');
        logs = data.logs || [];
        filterLogs();
        refreshState();
    } catch (error) {
        refreshState(true);
    } finally {
        refreshing = false;
    }
}
async function clearLogs() {
    if (clearing) return;
    clearing = true;
    try {
        if (!await confirmAction('将清空当前服务端日志记录，此操作无法撤销。', '清空运行日志')) return;
        await busy($('clear-btn'), async () => {
            await api.post('/api/logs/clear');
            await refreshLogs();
            showAlert('日志已清除', 'success');
        });
    } catch (error) {
        showAlert(errorMessage(error, '清空日志失败'), 'error');
    } finally {
        clearing = false;
    }
}
$('log-search').addEventListener('input', filterLogs);
$('log-level').addEventListener('change', filterLogs);
refreshLogs();
let logsTimer = setInterval(() => {
    if ($('auto-refresh').checked) refreshLogs();
}, 5000);
addEventListener('pagehide', () => clearInterval(logsTimer));

addEventListener('pageshow', event => { if (event.persisted) { refreshLogs(); logsTimer = setInterval(() => { if ($('auto-refresh').checked) refreshLogs(); }, 5000); } });
