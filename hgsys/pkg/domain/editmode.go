package domain

// EditMode 代表可編輯面板的編輯狀態.
type EditMode int

const (
	EditNone    EditMode = 0 // 顯示既有資料; 未在編輯.
	EditAppend  EditMode = 1 // 新增資料; 欄位可編輯, 以紅色顯示.
	EditModify  EditMode = 2 // 修改既有資料; 欄位可編輯, 以紅色顯示.
	EditInhibit EditMode = 3 // 因相鄰面板正在編輯, 故被鎖定.
)

// IsEditable 回報在指定模式下欄位是否應為可編輯.
func (m EditMode) IsEditable() bool {
	return m == EditAppend || m == EditModify
}
