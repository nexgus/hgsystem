package app

import (
	"context"
	"strings"

	"hgsys/pkg/repository"
)

// TitleService 為「客戶稱謂清單」的 Wails binding.
//
// 清單存放於 `titles` collection. 空字串 ("無稱謂") 不視為清單成員, 由前端固定提供.
type TitleService struct {
	repo *repository.TitleRepository
}

func NewTitleService(r *repository.Repositories) *TitleService {
	return &TitleService{repo: r.Titles}
}

// List 回傳目前已登錄的稱謂.
func (s *TitleService) List() ([]string, error) {
	return s.repo.List(context.Background())
}

// Add 將 name 加入清單. 前後空白會被去除; 加入空字串視為 no-op.
func (s *TitleService) Add(name string) error {
	return s.repo.Add(context.Background(), strings.TrimSpace(name))
}

// Remove 將 name 從清單移除. 不存在則為 no-op.
func (s *TitleService) Remove(name string) error {
	return s.repo.Remove(context.Background(), name)
}
