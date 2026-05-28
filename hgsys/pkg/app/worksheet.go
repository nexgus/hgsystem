package app

import (
	"context"
	"errors"

	"hgsys/pkg/domain"
	"hgsys/pkg/repository"
)

// WorksheetService binds the worksheet CRUD methods to the frontend.
type WorksheetService struct {
	repo *repository.WorksheetRepository
}

func NewWorksheetService(r *repository.Repositories) *WorksheetService {
	return &WorksheetService{repo: r.Worksheets}
}

// ListForCustomer returns all worksheets owned by cid (chronological / storage order).
func (s *WorksheetService) ListForCustomer(cid string) ([]domain.Worksheet, error) {
	return s.repo.FindForCustomer(context.Background(), cid)
}

// Insert persists a new worksheet. OrderTime is required (matches legacy validation).
func (s *WorksheetService) Insert(w domain.Worksheet) (string, error) {
	if w.OrderTime == nil {
		return "", errors.New("收件日不得為空白")
	}
	return s.repo.Insert(context.Background(), &w)
}

// Update overwrites the worksheet at id with the supplied values.
func (s *WorksheetService) Update(id string, w domain.Worksheet) error {
	if w.OrderTime == nil {
		return errors.New("收件日不得為空白")
	}
	return s.repo.Replace(context.Background(), id, w)
}

// Delete removes a single worksheet by id.
func (s *WorksheetService) Delete(id string) (int64, error) {
	return s.repo.Delete(context.Background(), id)
}

// DeleteForCustomer cascades deletion of all worksheets owned by cid.
// Exposed so the customer-delete UI can drive the cascade itself.
func (s *WorksheetService) DeleteForCustomer(cid string) (int64, error) {
	return s.repo.DeleteForCustomer(context.Background(), cid)
}
