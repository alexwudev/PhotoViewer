# PhotoViewer

仿 Windows 10 相片檢視器的輕量圖片檢視器，以 PyQt6 撰寫，支援 GIF／WebP 動圖與幻燈片播放。

## 功能

- 支援 jpg、png、bmp、gif、webp、tif、ico、svg
- 滑鼠滾輪縮放、放大後可拖曳平移；Ctrl+0 回到適合視窗
- 幻燈片（F5／F11／F12 全螢幕），間隔 1–30 秒八段可選，Space 暫停／繼續
- Delete 鍵：圖片移到資源回收筒，並自動切到下一張（幻燈片中亦可）
- 從檔案總管的**搜尋結果**開啟圖片時，會讀取該搜尋視窗的結果，跨資料夾瀏覽與播放幻燈片
- 排序一律依檔名自然排序（p1、p2、…、p10）

## 快捷鍵

| 按鍵 | 功能 |
| --- | --- |
| ← / → | 上一張／下一張 |
| Space | 幻燈片暫停／繼續（非幻燈片時為下一張） |
| F5 / F11 / F12 | 開始／停止全螢幕幻燈片 |
| Esc | 離開幻燈片或全螢幕 |
| Delete | 移到資源回收筒並顯示下一張 |
| Ctrl+O / Ctrl+Shift+O | 開啟圖片／開啟資料夾 |
| Ctrl+0 | 適合視窗 |

右鍵選單另有：幻燈片速率、開啟所在資料夾、複製圖片、刪除圖片。

---

## 在新電腦上重新安裝（從零開始）

電腦壞掉或重灌後，照下面順序做完即可恢復原本的使用方式。全部步驟約 10 分鐘，不需要系統管理員權限（全部裝在目前使用者底下）。

### 1. 安裝 Python 與 Git

- **Python 3.10 以上**：到 <https://www.python.org/downloads/windows/> 下載安裝程式。
  安裝第一個畫面**一定要勾選「Add python.exe to PATH」**，否則第 3 步的打包腳本找不到 Python。
- **Git**：到 <https://git-scm.com/download/win> 下載安裝，選項全部用預設值即可。
  （不想裝 Git 的話，可在 GitHub 頁面按 Code → Download ZIP，解壓縮後跳到第 3 步。）

裝好後開一個新的命令提示字元，確認兩個指令都有反應：

```
python --version
git --version
```

### 2. 下載原始碼

```
git clone https://github.com/alexwudev/PhotoViewer.git
```

放在哪裡都可以（例如桌面）。之後的步驟都在這個 `PhotoViewer` 資料夾裡做。

### 3. 打包並安裝

在資料夾裡按兩下 **`photo_viewer_build.bat`**。它會依序：

1. 用 pip 安裝 PyQt6、pyinstaller、comtypes；
2. 用 PyInstaller 打包成 `dist\PhotoViewer\PhotoViewer.exe`；
3. 把整個程式複製到 `%LOCALAPPDATA%\PhotoViewer\`（即 `C:\Users\<你的帳號>\AppData\Local\PhotoViewer\`）。

看到 `Done! Installed to: ...PhotoViewer.exe` 就成功了，按任意鍵關閉視窗。
打包需要一兩分鐘，期間畫面捲動很多訊息是正常的。

### 4. 註冊到「開啟檔案」清單

按兩下 **`photo_viewer_register.reg`**，出現登錄編輯程式的警告時按「是」。
這一步會：

- 讓 PhotoViewer 出現在圖片的右鍵「開啟檔案」清單裡；
- 保留檔案總管的圖片縮圖（不會全部變成程式圖示）。

檔案裡的路徑寫成 `%LOCALAPPDATA%`，任何帳號名稱都適用，不必修改。

### 5. 重新啟動檔案總管

工作管理員 → 找到「Windows 檔案總管」→ 右鍵「重新啟動」（或直接登出再登入）。

### 6. 設為預設的看圖程式

對任一張圖片按右鍵 → **開啟檔案** → **選擇其他應用程式** → 選 **Photo Viewer** → 勾選 **「一律使用此應用程式開啟 .jpg 檔案」** → 確定。

每種副檔名要各設一次（.jpg、.jpeg、.png、.gif、.webp 等常用的設一下即可）。
也可以到「設定 → 應用程式 → 預設應用程式」一次調整。

### 7. 確認

- 按兩下一張圖片，應該用 PhotoViewer 開啟；
- 在檔案總管搜尋框輸入關鍵字，從結果開一張圖，標題列應出現「（搜尋結果）」字樣，按 → 會跨資料夾切換。

---

## 更新程式

改過 `photo_viewer.py` 或拉了新版之後：

```
git pull
```

再按兩下 `photo_viewer_build.bat` 重新打包安裝即可，不必重新匯入 `.reg`。
（若打包時出現檔案被占用的錯誤，先把所有開著的 PhotoViewer 視窗關掉。）

## 不打包、直接執行原始碼

```
pip install PyQt6 comtypes
python photo_viewer.py [圖片或資料夾路徑]
```

`comtypes` 只用於「搜尋結果跨資料夾」功能；沒裝也能執行，只是會退回單一資料夾模式。

## 疑難排解

| 狀況 | 處理方式 |
| --- | --- |
| 執行 bat 顯示找不到 `python` | 安裝 Python 時沒勾「Add to PATH」；重新執行安裝程式選 Modify 補勾，或重裝 |
| 右鍵「開啟檔案」清單沒有 Photo Viewer | 確認第 4 步有匯入 `.reg`，並重新啟動檔案總管 |
| 檔案總管縮圖變成程式圖示 | 重新匯入 `.reg` 後重新啟動檔案總管 |
| 從搜尋結果開圖，卻只能看同資料夾的圖 | 開圖時搜尋視窗必須還開著；搜尋尚未跑完時只會讀到當下已列出的結果 |
| 按 Delete 後想救回圖片 | 圖片在資源回收筒，右鍵「還原」即可 |

## 解除安裝

1. 刪除資料夾 `%LOCALAPPDATA%\PhotoViewer`。
2. 用登錄編輯程式（regedit）刪除下列機碼：
   - `HKEY_CURRENT_USER\Software\Classes\Applications\PhotoViewer.exe`
   - `HKEY_CURRENT_USER\Software\Classes\Applications\PhotoViewerWebp.exe`
   - `HKEY_CURRENT_USER\Software\Classes\PhotoViewer.Image`
3. 到「設定 → 應用程式 → 預設應用程式」把圖片改回其他程式。

## 檔案說明

| 檔案 | 用途 |
| --- | --- |
| `photo_viewer.py` | 主程式（單一檔案） |
| `photo_viewer_build.bat` | 安裝相依套件、打包、安裝到 `%LOCALAPPDATA%` |
| `PhotoViewer.spec` | PyInstaller 打包設定（`python -m PyInstaller --noconfirm PhotoViewer.spec`） |
| `photo_viewer_register.reg` | 註冊「開啟檔案」清單與縮圖設定 |
