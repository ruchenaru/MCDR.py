# TimedCommandPlugin.py
# 一個用於定時執行Minecraft命令的MCDReforged插件

import time
import threading
import json
import os
from datetime import datetime

PLUGIN_METADATA = {
    'id': 'TC-TimedCommand',
    'version': '1.0.0',
    'name': '定時命令插件',
    'description': '一個用於在Minecraft 1.12.2中定時執行命令的插件',
    'author': 'ChenRu',
    'link': 'https://github.com/ruchenaru/MCDR.py',
    'dependencies': { 
        'mcdreforged': '>=2.0.0'
    }
}

# 全局變量
timed_tasks = {}
# 格式: {"task_id": {"command": "命令", "interval": 間隔秒數, "last_executed": 上次執行時間, "enabled": 是否啟用, "next_task": 後續任務ID}}

config_path = 'config/timed_command.json'
timer_thread = None
stop_flag = False

# 插件加載時執行
def on_load(server, prev):
    global timer_thread, stop_flag
    server.logger.info('定時命令插件已加載!')
    
    # 創建配置目錄
    if not os.path.exists('config'):
        os.makedirs('config')
        server.logger.info('創建配置目錄: config')
    
    # 加載配置
    load_config(server)
    
    # 註冊命令
    try:
        register_commands(server)
        server.logger.info('命令註冊成功!')
    except Exception as e:
        server.logger.error(f'命令註冊失敗: {e}')
    
    # 啟動定時器線程
    try:
        stop_flag = False
        timer_thread = threading.Thread(target=timer_loop, args=(server,), daemon=True)
        timer_thread.start()
        server.logger.info('定時器線程啟動成功!')
    except Exception as e:
        server.logger.error(f'定時器線程啟動失敗: {e}')
    
    server.say('§a[定時命令插件] 插件已加載，使用 !!timer help 查看幫助')

# 插件卸載時執行
def on_unload(server):
    global timer_thread, stop_flag
    server.logger.info('定時命令插件已卸載!')
    
    # 停止定時器線程
    stop_flag = True
    if timer_thread and timer_thread.is_alive():
        timer_thread.join(1.0)  # 等待線程結束，最多1秒

# 加載配置
def load_config(server):
    global timed_tasks
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                timed_tasks = json.load(f)
            server.logger.info(f'已加載 {len(timed_tasks)} 個定時任務')
    except Exception as e:
        server.logger.error(f'加載配置失敗: {e}')
        timed_tasks = {}

# 保存配置
def save_config(server):
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(timed_tasks, f, ensure_ascii=False, indent=4)
        server.logger.info('定時任務配置已保存')
    except Exception as e:
        server.logger.error(f'保存配置失敗: {e}')

# 定時器循環
def timer_loop(server):
    global timed_tasks, stop_flag
    server.logger.info('定時器線程已啟動')
    
    while not stop_flag:
        try:
            current_time = time.time()
            
            # 檢查所有任務
            for task_id, task in list(timed_tasks.items()):
                if task['enabled']:
                    # 檢查是否需要執行
                    if 'last_executed' not in task:
                        server.logger.info(f'任務 {task_id} 首次執行')
                        task['last_executed'] = current_time
                    
                    time_since_last = current_time - task['last_executed']
                    time_to_next = task['interval'] - time_since_last
                    
                    # 如果距離下次執行還有10秒，發送通知
                    if 9.5 <= time_to_next <= 10.5:
                        server.say(f'§e[定時命令] 任務 {task_id} 將在10秒後開始執行')
                    
                    # 檢查是否需要執行
                    if time_since_last >= task['interval']:
                        # 發送開始執行通知
                        server.say(f'§b[定時命令] 開始執行任務: {task_id}')
                        server.logger.info(f'執行定時任務 {task_id}: {task["command"]} (間隔: {time_since_last:.1f}秒)')
                        
                        # 執行命令
                        success = False
                        try:
                            server.execute(task['command'])
                            server.say(f'§a[定時命令] 任務執行完成: {task_id}')
                            success = True
                        except Exception as e:
                            server.logger.error(f'執行命令失敗: {e}')
                            server.say(f'§c[定時命令] 任務執行失敗: {task_id} - {str(e)}')
                        
                        # 更新上次執行時間
                        task['last_executed'] = current_time
                        save_config(server)
                        
                        # 如果任務執行成功且有一次性後續命令，則執行
                        if success and 'after_command' in task and task['after_command']:
                            after_command = task['after_command']
                            server.logger.info(f'執行一次性後續命令: {after_command}')
                            server.say(f'§b[TCcommand] 開始執行後續命令: {task_id}')
                            try:
                                server.execute(after_command)
                                server.say(f'§a[TCcommand] 後續命令執行完成: {task_id}')
                            except Exception as e:
                                server.logger.error(f'執行一次性後續命令失敗: {e}')
                                server.say(f'§c[定時命令] 後續命令執行失敗: {task_id} - {str(e)}')
                        
                        # 如果任務執行成功且有後續任務，則執行後續任務
                        if success and 'next_task' in task and task['next_task']:
                            next_task_id = task['next_task']
                            if next_task_id in timed_tasks:
                                server.logger.info(f'觸發後續任務: {next_task_id}')
                                server.say(f'§b[TCcommand] 開始執行後續任務: {next_task_id}')
                                try:
                                    server.execute(timed_tasks[next_task_id]['command'])
                                    server.say(f'§a[TCcommand] 後續任務執行完成: {next_task_id}')
                                except Exception as e:
                                    server.logger.error(f'執行後續任務失敗: {e}')
                                    server.say(f'§c[TCcommand] 後續任務執行失敗: {next_task_id} - {str(e)}')
                            else:
                                server.logger.warning(f'後續任務 {next_task_id} 不存在')
                                server.say(f'§c[TCcommand] 後續任務不存在: {next_task_id}')
            
            # 休眠1秒
            time.sleep(1)
        except Exception as e:
            server.logger.error(f'定時器循環發生錯誤: {e}')
            time.sleep(5)  # 發生錯誤時等待較長時間再重試

# 註冊命令
def register_commands(server):
    try:
        from mcdreforged.api.command import Literal, Integer, Text, GreedyText
        from mcdreforged.api.types import CommandSource
        
        server.logger.info('開始註冊命令')
        
        # 創建命令樹
        root_node = Literal('!!timer')\
            .then(
                Literal('add')\
                .then(
                    Text('task_id')\
                    .then(
                        Integer('interval_minutes')\
                        .then(
                            GreedyText('command')\
                            .runs(lambda src, ctx: add_task(src, ctx, server))
                        )
                    )
                )
                .then(
                    Text('task_id')\
                    .then(
                        Integer('interval_minutes')\
                        .then(
                            Text('command')\
                            .then(
                                Text('next_task_id')\
                                .runs(lambda src, ctx: add_task_with_next(src, ctx, server))
                            )
                        )
                    )
                )
            )\
            .then(
                Literal('remove')\
                .then(
                    Text('task_id')\
                    .runs(lambda src, ctx: remove_task(src, ctx, server))
                )
            )\
            .then(
                Literal('list')
                .runs(lambda src, ctx: list_tasks(src, server))
            )\
            .then(
                Literal('enable')\
                .then(
                    Text('task_id')\
                    .runs(lambda src, ctx: enable_task(src, ctx, server, True))
                )
            )\
            .then(
                Literal('disable')\
                .then(
                    Text('task_id')\
                    .runs(lambda src, ctx: enable_task(src, ctx, server, False))
                )
            )\
            .then(
                Literal('link')\
                .then(
                    Text('task_id')\
                    .then(
                        Text('next_task_id')\
                        .runs(lambda src, ctx: link_task(src, ctx, server))
                    )
                )
            )\
            .then(
                Literal('unlink')\
                .then(
                    Text('task_id')\
                    .runs(lambda src, ctx: unlink_task(src, ctx, server))
                )
            )\
            .then(
                Literal('test')\
                .then(
                    Text('task_id')\
                    .runs(lambda src, ctx: test_task(src, ctx, server))
                )
            )\
            .then(
                Literal('help')
                .runs(lambda src, ctx: show_help(src, server))
            )\
            .runs(lambda src, ctx: show_help(src, server))  # 直接輸入!!timer也顯示幫助
        
        # 註冊命令
        server.register_command(root_node)
        server.logger.info('命令樹註冊成功')
        
        # 註冊幫助信息
        server.register_help_message('!!timer', '定時執行Minecraft命令')
        server.logger.info('幫助信息註冊成功')
    except Exception as e:
        server.logger.error(f'註冊命令時發生錯誤: {e}')
        import traceback
        server.logger.error(traceback.format_exc())

# 命令處理函數
def add_task(source, context, server):
    global timed_tasks
    task_id = context['task_id']
    interval_minutes = context['interval_minutes']
    command = context['command']
    
    # 檢查命令中是否包含後續命令（使用-分隔）
    command_parts = command.split('-', 1)
    main_command = command_parts[0].strip()
    after_command = command_parts[1].strip() if len(command_parts) > 1 else ''
    
    # 檢查任務ID是否已存在
    if task_id in timed_tasks:
        server.reply(source, f'§c任務ID "{task_id}" 已存在，請使用其他ID')
        return
    
    # 添加新任務
    timed_tasks[task_id] = {
        'command': main_command,
        'interval': interval_minutes * 60,  # 轉換為秒
        'last_executed': time.time(),
        'enabled': True,
        'next_task': '',  # 初始化後續任務為空
        'after_command': after_command  # 添加後續命令
    }
    
    # 保存配置
    save_config(server)
    
    if after_command:
        server.reply(source, f'§a已添加定時任務 "{task_id}"，每 {interval_minutes} 分鐘執行一次: {main_command}，執行完成後將執行一次: {after_command}')
    else:
        server.reply(source, f'§a已添加定時任務 "{task_id}"，每 {interval_minutes} 分鐘執行一次: {main_command}')

def add_task_with_next(source, context, server):
    global timed_tasks
    task_id = context['task_id']
    interval_minutes = context['interval_minutes']
    command = context['command']
    next_task_id = context['next_task_id']
    
    # 檢查任務ID是否已存在
    if task_id in timed_tasks:
        server.reply(source, f'§c任務ID "{task_id}" 已存在，請使用其他ID')
        return
    
    # 添加新任務
    timed_tasks[task_id] = {
        'command': command,
        'interval': interval_minutes * 60,  # 轉換為秒
        'last_executed': time.time(),
        'enabled': True,
        'next_task': next_task_id  # 設置後續任務
    }
    
    # 保存配置
    save_config(server)
    
    server.reply(source, f'§a已添加定時任務 "{task_id}"，每 {interval_minutes} 分鐘執行一次: {command}，執行完成後將執行任務: {next_task_id}')

def remove_task(source, context, server):
    global timed_tasks
    task_id = context['task_id']
    
    # 檢查任務ID是否存在
    if task_id not in timed_tasks:
        server.reply(source, f'§c任務ID "{task_id}" 不存在')
        return
    
    # 刪除任務
    del timed_tasks[task_id]
    
    # 保存配置
    save_config(server)
    
    server.reply(source, f'§a已刪除定時任務 "{task_id}"')

def list_tasks(source, server):
    if not timed_tasks:
        server.reply(source, '§e目前沒有定時任務')
        return
    
    server.reply(source, '§6定時任務列表:')
    for task_id, task in timed_tasks.items():
        status = '§a啟用' if task['enabled'] else '§c禁用'
        interval_minutes = task['interval'] / 60
        last_time = datetime.fromtimestamp(task['last_executed']).strftime('%Y-%m-%d %H:%M:%S') if 'last_executed' in task else '從未'
        next_task = f'§f- 後續任務: §d{task["next_task"]}' if 'next_task' in task and task['next_task'] else ''
        server.reply(source, f'§6[{task_id}] {status} §f- 間隔: §b{interval_minutes}§f分鐘 - 上次執行: §b{last_time}§f - 命令: §e{task["command"]}{next_task}')

def enable_task(source, context, server, enable):
    global timed_tasks
    task_id = context['task_id']
    
    # 檢查任務ID是否存在
    if task_id not in timed_tasks:
        server.reply(source, f'§c任務ID "{task_id}" 不存在')
        return
    
    # 更新任務狀態
    timed_tasks[task_id]['enabled'] = enable
    
    # 保存配置
    save_config(server)
    
    status = '啟用' if enable else '禁用'
    server.reply(source, f'§a已{status}定時任務 "{task_id}"')

def link_task(source, context, server):
    global timed_tasks
    task_id = context['task_id']
    next_task_id = context['next_task_id']
    
    # 檢查任務ID是否存在
    if task_id not in timed_tasks:
        server.reply(source, f'§c任務ID "{task_id}" 不存在')
        return
    
    # 檢查後續任務ID是否存在
    if next_task_id not in timed_tasks:
        server.reply(source, f'§c後續任務ID "{next_task_id}" 不存在')
        return
    
    # 檢查是否自我引用
    if task_id == next_task_id:
        server.reply(source, f'§c不能將任務設置為自己的後續任務')
        return
    
    # 設置後續任務
    timed_tasks[task_id]['next_task'] = next_task_id
    
    # 保存配置
    save_config(server)
    
    server.reply(source, f'§a已將任務 "{task_id}" 的後續任務設置為 "{next_task_id}"')

def unlink_task(source, context, server):
    global timed_tasks
    task_id = context['task_id']
    
    # 檢查任務ID是否存在
    if task_id not in timed_tasks:
        server.reply(source, f'§c任務ID "{task_id}" 不存在')
        return
    
    # 檢查是否有後續任務
    if 'next_task' not in timed_tasks[task_id] or not timed_tasks[task_id]['next_task']:
        server.reply(source, f'§c任務 "{task_id}" 沒有設置後續任務')
        return
    
    # 移除後續任務
    next_task = timed_tasks[task_id]['next_task']
    timed_tasks[task_id]['next_task'] = ''
    
    # 保存配置
    save_config(server)
    
    server.reply(source, f'§a已移除任務 "{task_id}" 的後續任務 "{next_task}"')

def test_task(source, context, server):
    global timed_tasks
    task_id = context['task_id']
    
    # 檢查任務ID是否存在
    if task_id not in timed_tasks:
        server.reply(source, f'§c任務ID "{task_id}" 不存在')
        return
    
    # 獲取任務信息
    task = timed_tasks[task_id]
    
    # 顯示任務信息
    server.reply(source, f'§6測試執行任務 "{task_id}": {task["command"]}')
    
    # 執行命令
    success = False
    try:
        server.say(f'§b[定時命令] 測試執行任務: {task_id}')
        server.execute(task['command'])
        server.say(f'§a[定時命令] 測試任務執行完成: {task_id}')
        success = True
    except Exception as e:
        server.logger.error(f'測試執行命令失敗: {e}')
        server.reply(source, f'§c測試執行失敗: {str(e)}')
        server.say(f'§c[定時命令] 測試任務執行失敗: {task_id} - {str(e)}')
    
    # 如果任務執行成功且有一次性後續命令，則執行
    if success and 'after_command' in task and task['after_command']:
        after_command = task['after_command']
        server.reply(source, f'§6測試執行一次性後續命令: {after_command}')
        try:
            server.say(f'§b[定時命令] 測試執行一次性後續命令: {task_id}')
            server.execute(after_command)
            server.say(f'§a[定時命令] 測試一次性後續命令執行完成: {task_id}')
        except Exception as e:
            server.logger.error(f'測試執行一次性後續命令失敗: {e}')
            server.reply(source, f'§c測試執行一次性後續命令失敗: {str(e)}')
            server.say(f'§c[定時命令] 測試一次性後續命令執行失敗: {task_id} - {str(e)}')
    
    # 如果任務執行成功且有後續任務，則遞歸測試執行後續任務
    if success and 'next_task' in task and task['next_task']:
        next_task_id = task['next_task']
        if next_task_id in timed_tasks:
            server.reply(source, f'§6測試執行後續任務: {next_task_id}')
            try:
                server.say(f'§b[定時命令] 測試執行後續任務: {next_task_id}')
                server.execute(timed_tasks[next_task_id]['command'])
                server.say(f'§a[定時命令] 測試後續任務執行完成: {next_task_id}')
                
                # 遞歸測試後續任務的後續任務
                if 'next_task' in timed_tasks[next_task_id] and timed_tasks[next_task_id]['next_task']:
                    next_next_task_id = timed_tasks[next_task_id]['next_task']
                    context['task_id'] = next_next_task_id
                    test_task(source, context, server)
            except Exception as e:
                server.logger.error(f'測試執行後續任務失敗: {e}')
                server.reply(source, f'§c測試執行後續任務失敗: {str(e)}')
                server.say(f'§c[定時命令] 測試後續任務執行失敗: {next_task_id} - {str(e)}')
        else:
            server.logger.warning(f'後續任務 {next_task_id} 不存在')
            server.reply(source, f'§c後續任務 "{next_task_id}" 不存在')
            server.say(f'§c[定時命令] 測試後續任務不存在: {next_task_id}')

def show_help(source, server):
    server.reply(source, '§6===== 定時命令插件幫助 =====')
    server.reply(source, '§b!!timer add <任務ID> <間隔分鐘> <命令> §f- 添加定時任務')
    server.reply(source, '§b!!timer add <任務ID> <間隔分鐘> <命令>-<後續命令> §f- 添加定時任務，並在主命令執行完成後立即執行一次後續命令')
    server.reply(source, '§b!!timer remove <任務ID> §f- 刪除定時任務')
    server.reply(source, '§b!!timer list §f- 列出所有定時任務')
    server.reply(source, '§b!!timer enable <任務ID> §f- 啟用定時任務')
    server.reply(source, '§b!!timer disable <任務ID> §f- 禁用定時任務')
    server.reply(source, '§b!!timer link <任務ID> <後續任務ID> §f- 設置任務成功後執行的後續任務')
    server.reply(source, '§b!!timer unlink <任務ID> §f- 移除任務的後續任務設置')
    server.reply(source, '§b!!timer test <任務ID> §f- 立即測試執行指定任務')
    server.reply(source, '§b!!timer help §f- 顯示此幫助信息')
    server.reply(source, '§6示例: §f!!timer add backup 30 save-all')
    server.reply(source, '§6說明: §f這將創建一個名為"backup"的任務，每30分鐘執行一次"save-all"命令')
    server.reply(source, '§6後續命令示例: §f!!timer add backup 30 save-all-say 備份完成')
    server.reply(source, '§6說明: §f這將創建一個名為"backup"的任務，每30分鐘執行一次"save-all"命令，完成後立即執行一次"say 備份完成"命令')
    server.reply(source, '§6任務鏈接示例: §f!!timer link backup notify')
    server.reply(source, '§6說明: §f這將設置當"backup"任務成功執行後，自動執行"notify"任務')
    server.reply(source, '§6測試任務示例: §f!!timer test backup')
    server.reply(source, '§6說明: §f這將立即測試執行"backup"任務，如果有後續命令或後續任務也會一併測試執行')
