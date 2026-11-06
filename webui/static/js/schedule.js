let loading = false,
    saving = false,
    dirty = false;
const form = $('schedule-form');
const type = () => form.querySelector('[name=schedule_type]:checked').value;

function switchType() {
    document.querySelectorAll('.schedule-config').forEach(el => {
        const active = el.id === type() + '-config';
        el.hidden = !active;
        el.style.display = '';
        el.querySelectorAll('input').forEach(input => {
            input.disabled = !active;
            input.required = active;
        });
    });
}

function summarize(s) {
    if (!s.enabled) return '定时任务未启用';
    if (s.type === 'interval') return `每 ${s.hours} 小时自动同步`;
    if (s.type === 'cron') return 'Cron · ' + s.cron;
    return '每天 ' + (s.time || '10:00') + ' 自动同步';
}

function renderSaved(s) {
    $('saved-summary').textContent = summarize(s);
    const jobs = $('jobs-list');
    jobs.replaceChildren();
    if (!s.jobs?.length) {
        jobs.append(node('p', '暂无已调度任务', 'empty'));
        return;
    }
    for (const job of s.jobs) {
        const item = node('div', undefined, 'job');
        item.append(node('strong', job.name), node('p', job.id), node('p', '下次执行'), node('time', job
            .next_run));
        jobs.append(item);
    }
}
async function loadSchedule(confirmReload = false) {
    if (loading || saving) return;
    if (confirmReload && dirty && !await confirmAction('重新加载会丢弃尚未保存的修改。', '重新加载计划')) return;
    loading = true;
    const button = form.querySelector('[type=submit]');
    button.disabled = true;
    try {
        const {
            data: s
        } = await api.get('/api/schedule');
        $('enabled').checked = !!s.enabled;
        const radio = form.querySelector(
            `[name=schedule_type][value="${['daily','interval','cron'].includes(s.type)?s.type:'daily'}"]`
            );
        radio.checked = true;
        $('daily_time').value = s.time || '10:00';
        $('interval_hours').value = s.hours || 6;
        $('cron_expr').value = s.cron || '0 10 * * *';
        switchType();
        renderSaved(s);
        dirty = false;
        $('form-state').textContent = '与已保存计划一致';
    } catch (error) {
        showAlert(errorMessage(error, '加载计划失败，请重试'), 'error');
        $('form-state').textContent = '计划未加载';
    } finally {
        loading = false;
        button.disabled = false;
    }
}
form.addEventListener('input', () => {
    dirty = true;
    $('form-state').textContent = '有未保存的修改，右侧仍显示生效计划';
    switchType();
});
form.addEventListener('submit', async e => {
    e.preventDefault();
    if (loading || saving || !form.reportValidity()) return;
    const config = {
        enabled: $('enabled').checked,
        type: type()
    };
    if (config.type === 'daily') config.time = $('daily_time').value;
    if (config.type === 'interval') config.hours = Number($('interval_hours').value);
    if (config.type === 'cron') {
        config.cron = $('cron_expr').value.trim();
        if (config.cron.split(/\s+/).length !== 5) {
            showAlert('Cron 表达式需要包含分、时、日、月、星期五个字段', 'error');
            return;
        }
    }
    saving = true;
    try {
        await busy(form.querySelector('[type=submit]'), async () => {
            const {
                data
            } = await api.post('/api/schedule', config);
            dirty = false;
            showAlert(data.message, 'success');
            $('form-state').textContent = '已保存，正在获取生效计划…';
            try {
                const {
                    data: s
                } = await api.get('/api/schedule');
                renderSaved(s);
                $('form-state').textContent = '与已保存计划一致';
            } catch (error) {
                showAlert('保存成功，但生效计划刷新失败，请重新加载。', 'error');
            }
        });
    } catch (error) {
        showAlert(errorMessage(error, '保存计划失败'), 'error');
    } finally {
        saving = false;
    }
});
addEventListener('beforeunload', e => {
    if (dirty) {
        e.preventDefault();
        e.returnValue = '';
    }
});
switchType();
loadSchedule();
