package services

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
)

// settingsAppDir / settingsFilename 決定設定檔位置: <UserConfigDir>/hgsystem/
// settings.json. UserConfigDir 在 macOS 為 ~/Library/Application Support, 在
// Windows 為 %AppData% (Roaming). 與 log 目錄刻意分開 — log 是 state, 這裡是偏好.
const (
	settingsAppDir   = "hgsystem"
	settingsFilename = "settings.json"
)

// Settings 為持久化的使用者偏好. 目前僅記錄備份 / 還原對話框上次「成功」使用的
// 目錄, 供下次開啟對話框時作為起始目錄.
type Settings struct {
	BackupDir  string `json:"backupDir"`
	RestoreDir string `json:"restoreDir"`
}

// settingsMu 保護設定檔的 read-modify-write. 桌面單一使用者情境下競爭極少,
// 但 mutex 成本低, 可避免備份與還原同時寫入時互相覆蓋.
var settingsMu sync.Mutex

// settingsPath 回傳設定檔的完整路徑.
func settingsPath() (string, error) {
	base, err := os.UserConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(base, settingsAppDir, settingsFilename), nil
}

// LoadSettings 讀取設定檔. 檔案不存在或內容損毀時一律回傳零值 Settings (不報錯),
// 確保壞掉的設定檔不會阻擋備份 / 還原功能.
func LoadSettings() Settings {
	settingsMu.Lock()
	defer settingsMu.Unlock()
	return loadLocked()
}

// loadLocked 為不加鎖的讀取實作, 供 LoadSettings 與 update 共用 (兩者皆已持鎖).
func loadLocked() Settings {
	var s Settings
	path, err := settingsPath()
	if err != nil {
		return s
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return s
	}
	_ = json.Unmarshal(data, &s) // 損毀時維持零值.
	return s
}

// update 以 fn 修改現有設定後寫回. 為 read-modify-write, 不會覆寫其他欄位.
func update(fn func(*Settings)) error {
	settingsMu.Lock()
	defer settingsMu.Unlock()
	s := loadLocked()
	fn(&s)
	path, err := settingsPath()
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(&s, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o644)
}

// SaveBackupDir 記住備份對話框上次成功使用的目錄.
func SaveBackupDir(dir string) error {
	return update(func(s *Settings) { s.BackupDir = dir })
}

// SaveRestoreDir 記住還原對話框上次成功使用的目錄.
func SaveRestoreDir(dir string) error {
	return update(func(s *Settings) { s.RestoreDir = dir })
}
