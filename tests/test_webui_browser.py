"""Browser acceptance with mocked API responses; never runs a real sync.

Run: .venv/Scripts/python -m pytest tests/test_webui_browser.py -o addopts=''
Requires the optional playwright package and a local Chrome installation.
"""
import os
import threading
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

playwright = pytest.importorskip('playwright.sync_api')
from werkzeug.serving import make_server
from webui.app import app

CHROME = os.environ.get('WEBUI_BROWSER_PATH', r'C:\Program Files\Google\Chrome\Application\chrome.exe')


@pytest.fixture(scope='module')
def site():
    with TemporaryDirectory() as temp, patch('webui.app.CONFIG_PATH', Path(temp) / 'config.yaml'), patch('webui.app.SCHEDULE_CONFIG_PATH', Path(temp) / 'schedule.yaml'):
        server = make_server('127.0.0.1', 0, app)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        yield f'http://127.0.0.1:{server.server_port}'
        server.shutdown()
        thread.join()


@pytest.fixture
def browser_page(site):
    if not Path(CHROME).exists():
        pytest.skip('Set WEBUI_BROWSER_PATH to a Chromium browser executable')
    with playwright.sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME, headless=True)
        context = browser.new_context(viewport={'width':1440, 'height':1000})
        page = context.new_page()
        state = {
            'config': {'openlist':{'url':'http://openlist.example:5244','target_dir':'/Anime','update_timeout':180,'password':'demo','token':'demo-token'},'ani':{'rss_update':True},'http':{'timeout':45}},
            'schedule': {'enabled':True,'type':'daily','time':'10:00','jobs':[{'id':'demo','name':'每日更新','next_run':'2026-11-07 10:00:00'}]},
            'status': {'running':False,'last_run':'2026-11-06 09:00:00','last_result':{'success':True,'message':'任务执行成功'},'logs':[]},
            'logs':[{'time':'2026-11-06 09:00:00','level':'success','message':'任务执行完成'},{'time':'2026-11-06 08:59:00','level':'error','message':'<img src=x onerror="window.injected=true">连接失败'},{'time':'2026-11-06 08:58:00','level':'info','message':'开始同步 '+('long/path/'*30)}],
            'fail':set(), 'missing':set(), 'posts':[], 'gets':[],
        }
        state['status']['logs']=state['logs']
        def handle(route):
            request=route.request
            key=request.url.split('/api/')[1]
            if key in state['missing']:
                route.fulfill(status=404,json={'error':'配置文件不存在'})
                return
            if key in state['fail']:
                route.fulfill(status=500,json={'error':'模拟请求失败'})
                return
            if request.method=='POST':
                state['posts'].append((key,request.post_data_json))
                if key in ('config','schedule'):
                    data=request.post_data_json
                    if key=='schedule':data['jobs']=state['schedule']['jobs']
                    state[key]=data
                if key=='run':state['status']['running']=True
                if key=='logs/clear':state['logs']=[]
                route.fulfill(json={'success':True,'message':'保存成功'})
            else:
                state['gets'].append(key)
                route.fulfill(json={'logs':state['logs']} if key=='logs' else state[key])
        context.route('**/api/**',handle)
        page.on('dialog',lambda dialog: dialog.accept())
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        yield page,state,site,errors
        context.close()
        browser.close()


def test_pages_themes_and_responsive_layout(browser_page):
    page,state,site,errors=browser_page
    state['logs']=[{'time':'2026-11-06 09:00:00','level':'success','message':'任务执行完成，OpenList 存储已更新。'},{'time':'2026-11-06 08:59:42','level':'info','message':'正在整理番剧目录 /Anime/2026/秋季'},{'time':'2026-11-06 08:59:30','level':'info','message':'RSS 订阅获取成功，开始检查最新内容。'},{'time':'2026-11-06 08:59:12','level':'warning','message':'部分资源暂无更新，将在下次同步时重新检查。'},{'time':'2026-11-06 08:59:00','level':'info','message':'同步任务已启动。'}]
    state['status']['logs']=state['logs']
    output=Path('exports/ui')
    output.mkdir(parents=True,exist_ok=True)
    for width in (1440,1024,390):
        page.set_viewport_size({'width':width,'height':1000})
        for theme in ('light','dark'):
            page.add_init_script(f"localStorage.setItem('theme','{theme}')")
            for path,name in (('/','dashboard'),('/config','config'),('/schedule','schedule'),('/logs','logs')):
                page.goto(site+path)
                page.wait_for_function("document.querySelector('#theme').value === '"+theme+"'")
                page.wait_for_timeout(100)
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),(width,theme,path)
                assert page.locator('h1').count()==1
                page.screenshot(path=str(output/f'{name}-{theme}-{width}.png'),full_page=True)
    assert not errors


def test_dashboard_confirmation_failure_and_polling(browser_page):
    page,state,site,errors=browser_page
    page.goto(site)
    page.wait_for_function("document.querySelector('#task-status').textContent==='空闲'")
    assert page.locator('#next-run').inner_text()=='2026-11-07 10:00:00'
    page.locator('#run-btn').click()
    page.locator('#confirm-dialog button[value=cancel]').click()
    assert not state['posts']
    page.locator('#run-btn').click()
    page.locator('#confirm-submit').click()
    page.wait_for_function("document.querySelector('#task-status').textContent==='运行中'")
    assert page.locator('#run-btn').is_disabled()
    assert len([p for p in state['posts'] if p[0]=='run'])==1
    state['status']['running']=False
    state['status']['last_result']={'success':False,'message':'同步失败'}
    page.evaluate('refreshStatus()')
    assert page.locator('#result-badge').inner_text()=='执行失败'
    state['fail'].add('schedule')
    page.evaluate('refreshSchedule()')
    assert page.locator('#next-run').inner_text()=='2026-11-07 10:00:00'
    assert page.locator('#schedule-state').is_visible()
    state['fail'].add('status')
    page.evaluate('refreshStatus()')
    assert '刷新失败' in page.locator('#refresh-state').inner_text()
    assert page.locator('#last-result').inner_text()=='同步失败'
    assert not errors


def test_configuration_roundtrip_and_failure(browser_page):
    page,state,site,errors=browser_page
    page.goto(site+'/config')
    page.wait_for_function("document.querySelector('#form-state').textContent==='配置已加载'")
    assert page.locator('#openlist_update_timeout').input_value()=='180'
    assert page.locator('#http_timeout').input_value()=='45'
    assert page.locator('#openlist_token').get_attribute('type')=='password'
    page.get_by_role('button',name='显示 Token',exact=True).click()
    assert page.locator('#openlist_token').get_attribute('type')=='text'
    page.locator('#ani_rss_update').uncheck()
    page.locator('#ani_year').fill('2026')
    page.locator('#ani_rss_update').check()
    page.locator('#ani_rss_update').uncheck()
    assert page.locator('#ani_year').input_value()=='2026'
    page.locator('button[type=submit]').click()
    page.wait_for_function("document.querySelector('#form-state').textContent==='所有修改已保存'")
    assert state['config']['openlist']['update_timeout']==180
    assert state['config']['http']['timeout']==45
    assert state['config']['ani']['year']==2026
    state['fail'].add('config')
    page.locator('button[type=submit]').click()
    page.wait_for_function("document.querySelector('.alert-error')!==null")
    assert page.locator('#openlist_update_timeout').input_value()=='180'
    assert not errors


def test_schedule_modes_and_saved_summary(browser_page):
    page,state,site,errors=browser_page
    page.goto(site+'/schedule')
    page.wait_for_function("document.querySelector('#form-state').textContent==='与已保存计划一致'")
    for mode in ('interval','cron','daily'):
        page.locator(f'[name=schedule_type][value={mode}]').check()
        if mode=='interval':page.locator('#interval_hours').fill('8')
        if mode=='cron':page.locator('#cron_expr').fill('0 12 * * *')
        assert '有未保存' in page.locator('#form-state').inner_text()
        page.locator('button[type=submit]').click()
        page.wait_for_function("document.querySelector('#form-state').textContent==='与已保存计划一致'")
        assert state['schedule']['type']==mode
    assert '2026-11-07 10:00:00' in page.locator('#jobs-list').inner_text()
    state['fail'].add('schedule')
    page.locator('button[type=submit]').click()
    page.wait_for_function("document.querySelector('.alert-error')!==null")
    assert '每天' in page.locator('#saved-summary').inner_text()
    assert not errors


def test_logs_filter_refresh_clear_and_text_safety(browser_page):
    page,state,site,errors=browser_page
    page.goto(site+'/logs')
    page.wait_for_function("document.querySelectorAll('.log-row').length===3")
    assert page.locator('#logs-container img').count()==0
    assert page.evaluate('window.injected') is None
    page.locator('#log-level').select_option('error')
    assert page.locator('.log-row').count()==1
    page.locator('#log-search').fill('不存在')
    assert '没有符合' in page.locator('#logs-container').inner_text()
    page.locator('#log-search').fill('连接')
    assert page.locator('.log-row').count()==1
    state['fail'].add('logs')
    page.evaluate('refreshLogs()')
    assert page.locator('.log-row').count()==1
    state['fail'].clear()
    page.locator('#clear-btn').click()
    page.locator('#confirm-submit').click()
    page.wait_for_function("document.querySelectorAll('.log-row').length===0")
    assert not errors


def test_first_use_theme_and_mobile_keyboard(browser_page):
    page,state,site,errors=browser_page
    state['missing'].add('config')
    page.set_viewport_size({'width':390,'height':844})
    page.goto(site+'/config')
    page.wait_for_function("document.querySelector('.alert-error')!==null")
    assert '尚无配置文件' in page.locator('.alert-error').inner_text()
    assert page.locator('button[type=submit]').is_enabled()
    page.locator('#menu-toggle').click()
    assert page.locator('#menu-toggle').get_attribute('aria-expanded')=='true'
    page.keyboard.press('Escape')
    assert page.locator('#menu-toggle').get_attribute('aria-expanded')=='false'
    page.locator('#menu-toggle').click()
    page.locator('#theme').select_option('dark')
    page.reload()
    assert page.evaluate('document.documentElement.dataset.theme')=='dark'
    assert not errors


def test_request_deduplication_and_double_submit(browser_page):
    page,state,site,errors=browser_page
    page.goto(site+'/config')
    page.wait_for_function("document.querySelector('#form-state').textContent==='配置已加载'")
    before=len(state['gets'])
    page.evaluate("Promise.all([api.get('/api/config'),api.get('/api/config')])")
    assert len(state['gets'])==before+1
    page.evaluate("document.querySelector('#config-form').requestSubmit();document.querySelector('#config-form').requestSubmit()")
    page.wait_for_function("document.querySelector('#form-state').textContent==='所有修改已保存'")
    assert len(state['posts'])==1
    page.locator('#openlist_update_timeout').fill('0')
    page.locator('button[type=submit]').click()
    assert len(state['posts'])==1
    assert not errors
