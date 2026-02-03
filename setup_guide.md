# GitHub Copilot SDK .NET 10 單檔執行：完整安裝指南

這份指南整理了從零開始設定「.NET 10 單檔執行 (dotnet run file)」與「GitHub Copilot SDK」的完整流程。

---

## 📋 準備工作
1.  **GitHub 帳號**：需有有效的 GitHub Copilot 訂閱。
2.  **.NET 10 SDK**：請確保已安裝 .NET 10 以上版本。
    - 驗證：`dotnet --version` (應顯示 10.0.x)

---

## 🚀 第一步：安裝並設定 GitHub CLI (`gh`)

GitHub Copilot SDK 依賴 GitHub CLI 進行身分驗證。

1.  **安裝 GitHub CLI**：
    開啟 PowerShell 執行：
    ```powershell
    winget install GitHub.cli
    ```
2.  **身分登入**：
    執行指令並依照瀏覽器提示完成授權：
    ```powershell
    gh auth login
    ```
    - 選項建議：`GitHub.com` -> `HTTPS/SSH` -> `Login with a web browser`。

---

## 🛠️ 第二步：安裝獨立版 Copilot CLI (關鍵)

> [!IMPORTANT]
> **請勿使用** 舊版的 `gh extension install github/gh-copilot`，該擴充功能已停止支援。SDK 需要的是**獨立版 (Standalone)** 的 CLI。

1.  **移除舊版 (若曾安裝過)**：
    ```powershell
    gh extension remove copilot
    ```
2.  **安裝獨立版**：
    ```powershell
    winget install GitHub.Copilot
    ```
3.  **重新啟動終端機**：安裝完後請務必關閉並重新開啟 VS Code 或 PowerShell，以確保系統抓到新的 `copilot` 路徑。

---

## 📝 第三步：設定 C# 單一檔案程式碼

建立一個 `Program.cs` 檔案，並在最頂部加入 .NET 10 的指示詞（Directives）。這可以取代傳統的 `.csproj` 檔案。

```csharp
#!/usr/bin/dotnet run
#:sdk Microsoft.NET.Sdk
#:property TargetFramework=net10.0
#:package GitHub.Copilot.SDK@0.1.20

using System;
using GitHub.Copilot.SDK;
using System.Threading;

// 以下為您的 Top-level statements 程式碼
Console.WriteLine("Initializing...");
// ... 您的其餘代碼
```

> [!TIP]
> 如果您的資料夾中本來就有 `.csproj` 檔案，請將它重新命名（例如改為 `.bak`），否則 `dotnet run` 會優先讀取專案檔而導致單檔指示詞失效。

---

## 🏃 第四步：執行程式

在終端機中切換至該目錄，直接執行：

```powershell
dotnet run .\Program.cs
```

---

## 🔍 常見問題故障排除 (Troubleshooting)

### 1. 「檔案正由另一個程序使用」 (File Lock)
**現象**：出現 `The process cannot access the file ... Program.dll`。
**原因**：之前的程式還在背景執行，導致檔案被鎖定。
**解法**：執行以下指令強行終端背景程序：
```powershell
Stop-Process -Name "Program", "dotnet" -Force -ErrorAction SilentlyContinue
```

### 2. 「連線在要求完成之前已中斷」 (JSON-RPC Error)
**原因**：這通常發生在系統仍在使用舊版 `gh-copilot` 擴充功能，或是 `copilot` 獨立版未正確安裝於 PATH 中。
**解法**：確認已執行 `gh extension remove copilot` 並完成「獨立版」安裝。

### 3. 無法辨識 `copilot` 指令
**解法**：手動將 WinGet 安裝路徑加入系統環境變數。
常見路徑為：
`%LocalAppData%\Microsoft\WinGet\Packages\GitHub.Copilot_Microsoft.Winget.Source_8wekyb3d8bbwe`
