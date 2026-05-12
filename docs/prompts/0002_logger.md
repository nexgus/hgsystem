仿 ~/myproj/cheese/ 的風格/方式, 加入 logger. 有什麼問題得先問我

-----
1. 使用 YYMMDD_{9999}.log, 其中 {9999} 指的是流水號, 由 0001 開始編號. 每次執行 hgsys, 都要決定這次的流水號.
2. 加入 --debug/-d, 不用 --verbose/-v.
3. 依你的建議
4. 合併成單一目錄
5. 拿掉 dry run.
6. 保持原樣.

-----
將 logs/ 目錄改成 Windows/macOS 的習慣目錄
- macOS: `~/Library/Logs/hgsystem/YYMMDD_NNNN.log`
- Windows: `%LOCALAPPDATA%\hgsystem\logs\YYMMDD_NNNN.log` (e.g. `C:\Users\<user>\AppData\Local\hgsystem\logs\`)
- Linux fallback: `$XDG_STATE_HOME/hgsystem/logs/` 或 `~/.local/state/hgsystem/logs/`