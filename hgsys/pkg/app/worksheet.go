package app

import (
	"context"
	"errors"

	"hgsys/pkg/domain"
	"hgsys/pkg/repository"
)

// WorksheetService 將 worksheet CRUD 方法 binding 至 frontend.
type WorksheetService struct {
	repo *repository.WorksheetRepository
}

func NewWorksheetService(r *repository.Repositories) *WorksheetService {
	return &WorksheetService{repo: r.Worksheets}
}

// ListForCustomer 回傳 cid 所屬之所有 worksheet (依時間 / 儲存順序).
func (s *WorksheetService) ListForCustomer(cid string) ([]domain.Worksheet, error) {
	return s.repo.FindForCustomer(context.Background(), cid)
}

// Insert 保存一筆新的 worksheet. OrderTime 為必填 (對齊舊版驗證規則).
func (s *WorksheetService) Insert(w domain.Worksheet) (string, error) {
	if w.OrderTime == nil {
		return "", errors.New("收件日不得為空白")
	}
	return s.repo.Insert(context.Background(), &w)
}

// Update 以給定的資料覆寫指定 id 的 worksheet.
func (s *WorksheetService) Update(id string, w domain.Worksheet) error {
	if w.OrderTime == nil {
		return errors.New("收件日不得為空白")
	}
	return s.repo.Replace(context.Background(), id, w)
}

// Delete 依 id 刪除單一 worksheet.
func (s *WorksheetService) Delete(id string) (int64, error) {
	return s.repo.Delete(context.Background(), id)
}

// DeleteForCustomer 串聯刪除 cid 所屬之所有 worksheet.
// 暴露此方法是為了讓「刪除客戶」UI 能自行驅動串聯刪除.
func (s *WorksheetService) DeleteForCustomer(cid string) (int64, error) {
	return s.repo.DeleteForCustomer(context.Background(), cid)
}
