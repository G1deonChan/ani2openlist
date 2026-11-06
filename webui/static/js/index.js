let refreshInFlight = false,
    runPending = false;
async function refreshStatus() {
    if (refreshInFlight) return;
    refreshInFlight = true;
    try {
        const {
            data: status
        } = await api.get('/api/status');
        $('task-status').textContent = status.running ? '运行中' : '空闲';
        $('task-status').className = status.running ? 'status-running' : '';
        $('run-btn').disabled = status.running || runPending;
        $('last-run').textContent = status.last_run || '从未运行';
        $('last-result').textContent = status.last_result?.message || '尚未运行任务，配置完成后即可开始同步。';
        $('result-badge').textContent = status.last_result ? (status.last_result.success ? '执行成功' :
            '执行失败') : '等待同步';
        $('result-badge').className = 'badge ' + (status.last_result ? (status.last_result.success ?
            'success' : 'error') : '');
        renderLogs($('recent-logs'), (status.logs || []).slice(0, 5));
        refreshState();
    } catch (error) {
        refreshState(true);
    } finally {
        refreshInFlight = false;
    }
}
async function refreshSchedule() {
    try {
        const {
            data: s
        } = await api.get('/api/schedule');
        $('schedule-state').hidden = true;
        $('next-run').textContent = !s.enabled ? '未启用' : s.jobs?.[0]?.next_run || '暂无已调度任务';
    } catch (error) {
        if ($('next-run').textContent === '加载中…') $('next-run').textContent = '暂不可用';
        $('schedule-state').textContent = '计划刷新失败，将自动重试';
        $('schedule-state').hidden = false;
    }
}
async function runTask() {
    if (runPending || $('run-btn').disabled) return;
    runPending = true;
    try {
        if (!await confirmAction('将使用已保存的配置开始同步，是否继续？', '运行同步任务')) return;
        $('run-btn').disabled = true;
        const {
            data
        } = await api.post('/api/run');
        showAlert(data.message, 'success');
    } catch (error) {
        showAlert(errorMessage(error, '运行任务失败'), 'error');
    } finally {
        runPending = false;
        await refreshStatus();
    }
}
refreshStatus();
refreshSchedule();
let statusTimer = setInterval(refreshStatus, 2000),
    scheduleTimer = setInterval(refreshSchedule, 30000);
addEventListener('pagehide', () => {
    clearInterval(statusTimer);
    clearInterval(scheduleTimer);
});

addEventListener('pageshow', event => { if (event.persisted) { refreshStatus(); refreshSchedule(); statusTimer = setInterval(refreshStatus, 2000); scheduleTimer = setInterval(refreshSchedule, 30000); } });
