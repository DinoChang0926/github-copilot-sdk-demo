# GitHub Copilot SDK Demo - Multi-Agent System

這是一個使用 GitHub Copilot SDK 建構的「多代理人協作系統 (Multi-Agent System)」。
系統包含「Worker Agent」與「Reviewer Agent」，能夠自動化地撰寫程式碼並進行自我審核，直到品質達標。此外，系統整合了「Repository Skill」，能夠直接 Clone 指定的 GitHub 儲存庫並在其中工作。

## 📁 專案結構

```text
github-copilot-sdk-demo/
├── src/                        # 核心程式碼
│   ├── multi_agent.py          # 多代理人系統邏輯 (Worker + Reviewer loop)
│   └── skills/                 # 技能模組
│       └── repository.py       # Git 儲存庫操作技能
├── examples/                   # 範例程式
│   ├── event_driven.py         # 事件驅動架構範例
│   └── multi_agent_usage.py    # 多代理人組件呼叫範例
├── main.py                     # 互動式主程式 (Entry Point)
├── requirements.txt            # 相依套件清單
└── README.md                   # 說明文件
```

## 🚀 快速開始

### 1. 安裝需求
確保您已安裝 GitHub Copilot CLI (Standalone) 與 Python 環境。

```bash
pip install -r requirements.txt
```

### 2. 設定環境變數
請在專案根目錄建立 `.env` 檔案（參考 `.env.example`）：

```ini
# .env
COPILOT_MODEL=claude-3.5-sonnet
# 如果需要，這裏可以設定其他變數
```

### 3. 執行主程式
啟動互動式介面：

```bash
python main.py
```

## 💡 使用方式

當程式啟動後，您可以：

1.  **輸入需求**: 例如「幫我寫一個 Python 費氏數列函式」。
2.  **指定 Repo (選填)**: 系統會詢問是否要 Clone 特定的 GitHub Repo。
    *   若提供 URL，Worker Agent 會先 Clone 下來，然後根據您的需求修改該專案。
    *   若留空，Worker 會直接針對您的需求產生新程式碼。

### 系統運作流程
1.  **Worker Agent**: 接收您的 Prompt，若有 Repo 則先執行 Clone，接著撰寫/修改程式碼。
2.  **Reviewer Agent**: 根據您的原始要求，檢查 Worker 的產出是否合格。
3.  **Feedback Loop**: 若不合格，Reviewer 會提出修正建議，Worker 修正後再次提交（最多重試 3 次）。

## 📚 進階開發

如果您想將此系統整合到其他專案，可以參考 `examples/multi_agent_usage.py`：

```python
from copilot import CopilotClient
from src.multi_agent import MultiAgentTask

async with CopilotClient() as client:
    task = MultiAgentTask(client)
    result = await task.run("您的需求")
    
    if result.success:
        print(result.code)
```

## 📝 授權
MIT License
