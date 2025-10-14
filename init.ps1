# Ani2Openlist 快速初始化脚本
# 用于首次部署时设置配置文件

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "🎬 Ani2Openlist 初始化向导" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# 检查配置文件
if (Test-Path "config.yaml") {
    Write-Host "⚠️  config.yaml 已存在" -ForegroundColor Yellow
    $overwrite = Read-Host "是否覆盖？(y/N)"
    if ($overwrite -ne "y") {
        Write-Host "跳过 config.yaml" -ForegroundColor Gray
        $createConfig = $false
    } else {
        $createConfig = $true
    }
} else {
    $createConfig = $true
}

if ($createConfig) {
    Write-Host "📝 创建 config.yaml..." -ForegroundColor Green
    Copy-Item "config.yaml.example" "config.yaml"
    Write-Host "✅ config.yaml 已创建" -ForegroundColor Green
    Write-Host "   请编辑此文件并填写你的 Openlist 配置" -ForegroundColor Gray
}

Write-Host ""

# 检查 Web UI 配置
if (Test-Path "webui/schedule.yaml") {
    Write-Host "⚠️  webui/schedule.yaml 已存在" -ForegroundColor Yellow
    $overwrite = Read-Host "是否覆盖？(y/N)"
    if ($overwrite -ne "y") {
        Write-Host "跳过 webui/schedule.yaml" -ForegroundColor Gray
        $createSchedule = $false
    } else {
        $createSchedule = $true
    }
} else {
    $createSchedule = $true
}

if ($createSchedule) {
    Write-Host "📝 创建 webui/schedule.yaml..." -ForegroundColor Green
    Copy-Item "webui/schedule.yaml.example" "webui/schedule.yaml"
    Write-Host "✅ webui/schedule.yaml 已创建" -ForegroundColor Green
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ 初始化完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📋 后续步骤：" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. 编辑配置文件：" -ForegroundColor White
Write-Host "   notepad config.yaml" -ForegroundColor Gray
Write-Host ""
Write-Host "2. 安装依赖：" -ForegroundColor White
Write-Host "   pip install -r requirements.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "3. 测试配置：" -ForegroundColor White
Write-Host "   python test_setup.py" -ForegroundColor Gray
Write-Host ""
Write-Host "4. 启动 Web UI：" -ForegroundColor White
Write-Host "   python webui_start.py" -ForegroundColor Gray
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "⚠️  安全提示：" -ForegroundColor Red
Write-Host "   - config.yaml 包含敏感信息，不要提交到 Git" -ForegroundColor Yellow
Write-Host "   - 推送到 GitHub 前请运行: python check_privacy.py" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
