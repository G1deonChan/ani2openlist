#!/bin/bash
# Ani2Openlist 快速初始化脚本（Linux/Mac）
# 用于首次部署时设置配置文件

echo "============================================================"
echo "🎬 Ani2Openlist 初始化向导"
echo "============================================================"
echo ""

# 检查配置文件
if [ -f "config.yaml" ]; then
    echo "⚠️  config.yaml 已存在"
    read -p "是否覆盖？(y/N) " overwrite
    if [ "$overwrite" != "y" ]; then
        echo "跳过 config.yaml"
        createConfig=false
    else
        createConfig=true
    fi
else
    createConfig=true
fi

if [ "$createConfig" = true ]; then
    echo "📝 创建 config.yaml..."
    cp config.yaml.example config.yaml
    echo "✅ config.yaml 已创建"
    echo "   请编辑此文件并填写你的 Openlist 配置"
fi

echo ""

# 检查 Web UI 配置
if [ -f "webui/schedule.yaml" ]; then
    echo "⚠️  webui/schedule.yaml 已存在"
    read -p "是否覆盖？(y/N) " overwrite
    if [ "$overwrite" != "y" ]; then
        echo "跳过 webui/schedule.yaml"
        createSchedule=false
    else
        createSchedule=true
    fi
else
    createSchedule=true
fi

if [ "$createSchedule" = true ]; then
    echo "📝 创建 webui/schedule.yaml..."
    cp webui/schedule.yaml.example webui/schedule.yaml
    echo "✅ webui/schedule.yaml 已创建"
fi

echo ""
echo "============================================================"
echo "✅ 初始化完成！"
echo "============================================================"
echo ""
echo "📋 后续步骤："
echo ""
echo "1. 编辑配置文件："
echo "   nano config.yaml"
echo ""
echo "2. 安装依赖："
echo "   pip install -r requirements.txt"
echo ""
echo "3. 测试配置："
echo "   python test_setup.py"
echo ""
echo "4. 启动 Web UI："
echo "   python webui_start.py"
echo ""
echo "============================================================"
echo "⚠️  安全提示："
echo "   - config.yaml 包含敏感信息，不要提交到 Git"
echo "   - 推送到 GitHub 前请运行: python check_privacy.py"
echo "============================================================"
echo ""
