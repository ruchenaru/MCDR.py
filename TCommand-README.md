# MCDReforged 定時命令插件

這是一個用於Minecraft 1.12.2的MCDReforged插件，可以讓你設置定時執行的Minecraft命令。

## 功能

- 設置定時執行的Minecraft命令
- 支持以分鐘為單位的時間間隔
- 可以啟用/禁用定時任務
- 支持任務鏈接，一個任務成功執行後自動觸發另一個任務
- 設置成功後在聊天頻道發送通知
- 任務即將開始時（提前10秒）在聊天頻道發送通知
- 任務開始執行和執行完畢時在聊天頻道發送通知
- 支持測試執行任務功能
- 配置自動保存，服務器重啟後仍然有效

## 安裝

1. 將`TimedCommandPlugin.py`文件放入MCDReforged的`plugins`目錄中
2. 重啟MCDReforged或使用`!!MCDR reload`命令加載插件

## 命令

### 添加定時任務

```
!!timer add <任務ID> <間隔分鐘> <命令>
```

- `<任務ID>`: 任務的唯一標識符，用於後續管理
- `<間隔分鐘>`: 執行命令的時間間隔，以分鐘為單位
- `<命令>`: 要執行的Minecraft命令

示例：
```
!!timer add backup 30 save-all
```
這將創建一個名為"backup"的任務，每30分鐘執行一次"save-all"命令。

### 刪除定時任務

```
!!timer remove <任務ID>
```

示例：
```
!!timer remove backup
```

### 列出所有定時任務

```
!!timer list
```

### 啟用定時任務

```
!!timer enable <任務ID>
```

### 禁用定時任務

```
!!timer disable <任務ID>
```

### 設置任務鏈接

```
!!timer link <任務ID> <後續任務ID>
```

設置一個任務在成功執行後自動觸發另一個任務。

示例：
```
!!timer link backup announce
```
這將設置當"backup"任務成功執行後，自動執行"announce"任務。

### 移除任務鏈接

```
!!timer unlink <任務ID>
```

示例：
```
!!timer unlink backup
```

### 測試執行任務

```
!!timer test <任務ID>
```

立即測試執行指定的任務，並在聊天頻道顯示執行結果。如果任務設置了後續任務，也會自動測試執行後續任務。

示例：
```
!!timer test backup
```

### 顯示幫助信息

```
!!timer help
```

## 配置文件

插件會自動在`config/timed_command.json`創建配置文件，保存所有定時任務的信息。配置文件格式如下：

```json
{
    "任務ID": {
        "command": "要執行的命令",
        "interval": "間隔秒數",
        "last_executed": "上次執行時間戳",
        "enabled": "true或false",
        "next_task": "後續任務ID或空字符串"
    },
    ...
}
```

## 使用場景

1. **定時備份**：每隔一段時間自動保存世界
   ```
   !!timer add backup 30 save-all
   ```

2. **定時公告**：每隔一段時間向所有玩家發送消息
   ```
   !!timer add announce 15 say 歡迎來到我們的服務器！
   ```

3. **定時執行遊戲內命令**：例如每小時給予所有玩家一些物品
   ```
   !!timer add reward 60 give @a minecraft:diamond 1
   ```

4. **任務鏈接**：備份完成後自動通知玩家
   ```
   !!timer add backup 30 save-all
   !!timer add notify 0 say 服務器備份已完成！
   !!timer link backup notify
   ```
   這將設置每30分鐘執行一次備份，備份成功後自動發送通知消息。

5. **定時重啟服務器**：每天定時重啟服務器（需要配合其他插件）
   ```
   !!timer add restart 1440 restart
   ```

## 注意事項

1. 插件使用多線程執行定時任務，不會阻塞主線程
2. 時間間隔的最小單位是分鐘，不支持秒級定時
3. 任務ID必須是唯一的，不能重複
4. 插件會自動保存配置，無需手動操作
5. 如果要執行複雜的命令序列，建議創建多個定時任務
6. 任務執行前10秒會在聊天頻道發送通知
7. 任務開始執行和執行完畢時會在聊天頻道發送通知，包含任務ID