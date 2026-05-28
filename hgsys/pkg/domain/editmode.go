package domain

// EditMode represents the editing state of an editable panel.
type EditMode int

const (
	EditNone    EditMode = 0 // Showing existing data; not editing.
	EditAppend  EditMode = 1 // Adding a new record; fields editable, drawn red.
	EditModify  EditMode = 2 // Modifying an existing record; fields editable, drawn red.
	EditInhibit EditMode = 3 // Locked because the sibling panel is editing.
)

// IsEditable reports whether fields should be editable in the given mode.
func (m EditMode) IsEditable() bool {
	return m == EditAppend || m == EditModify
}
