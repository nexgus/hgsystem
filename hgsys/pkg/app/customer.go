// Package app 內含暴露給 Vue frontend 的 Wails service binding.
//
// 每個 *Service 型別持有 repository / coordinator 參考, 並提供一組精簡的方法,
// 可透過 wails3 generate bindings 由 JS 呼叫. 方法回傳純粹值 (不含 Mongo /
// Wails 型別), 讓產生的 TS API 保持易讀.
package app

import (
	"context"
	"errors"
	"fmt"
	"sort"
	"time"

	"hgsys/pkg/domain"
	"hgsys/pkg/repository"
)

// CustomerService 為客戶 CRUD 方法的 binding. 協調狀態 (目前選取項目, 編輯模式)
// 完全交由 frontend store 管理 — Go 端僅負責回傳資料與保存變更.
type CustomerService struct {
	repo       *repository.CustomerRepository
	worksheets *repository.WorksheetRepository
	history    *repository.SearchHistoryRepository
}

func NewCustomerService(r *repository.Repositories) *CustomerService {
	return &CustomerService{
		repo:       r.Customers,
		worksheets: r.Worksheets,
		history:    r.SearchHistory,
	}
}

// Count 回傳客戶總數.
func (s *CustomerService) Count() (int64, error) {
	return s.repo.Count(context.Background())
}

// Get 回傳指定 id 的客戶, 若找不到則回傳 error.
func (s *CustomerService) Get(id string) (*domain.Customer, error) {
	c, err := s.repo.Get(context.Background(), id)
	if err != nil {
		return nil, err
	}
	if c == nil {
		return nil, fmt.Errorf("customer %s not found", id)
	}
	return c, nil
}

// Insert 保存一筆新客戶 (id 為空時自動產生).
func (s *CustomerService) Insert(c domain.Customer) (string, error) {
	if c.Name == "" {
		return "", errors.New("姓名不得為空白")
	}
	return s.repo.Insert(context.Background(), &c)
}

// Update 以給定的資料覆寫指定 id 的客戶.
func (s *CustomerService) Update(id string, c domain.Customer) error {
	if c.Name == "" {
		return errors.New("姓名不得為空白")
	}
	return s.repo.Replace(context.Background(), id, c)
}

// Delete 刪除該客戶, 並串聯刪除其所有 worksheet. 回傳一併被刪除的 worksheet 數.
func (s *CustomerService) Delete(id string) (int64, error) {
	if err := s.repo.Delete(context.Background(), id); err != nil {
		return 0, err
	}
	return s.worksheets.DeleteForCustomer(context.Background(), id)
}

// SearchService 獨立成型, 讓搜尋對話框擁有自己的 binding.
type SearchService struct {
	repo       *repository.CustomerRepository
	worksheets *repository.WorksheetRepository
	history    *repository.SearchHistoryRepository
}

func NewSearchService(r *repository.Repositories) *SearchService {
	return &SearchService{
		repo:       r.Customers,
		worksheets: r.Worksheets,
		history:    r.SearchHistory,
	}
}

// SearchCriteria 對應搜尋對話框的輸入欄位.
//
// DateField 為 "order" / "deliver" / "" — 指定要套用 worksheet 的接單日期或交貨
// 日期條件. 僅當 DateField 非空且 DateFrom / DateTo 至少一者非 nil 時, 期間條件
// 才會啟用; 啟用時會先查 worksheets 取得符合的 cid 集合, 再 AND 進 customer
// filter.
type SearchCriteria struct {
	Name      string     `json:"name"`
	Addr      string     `json:"addr"`
	Phone     string     `json:"phone"`
	Birthdate *time.Time `json:"birthdate"`
	DateField string     `json:"dateField"`
	DateFrom  *time.Time `json:"dateFrom"`
	DateTo    *time.Time `json:"dateTo"`
}

// Search 以子字串 regex 比對 name / addr / phone, 並以精確比對檢索 birthdate.
// 空欄位會被忽略. 若指定了工作單期間條件, 會跨 worksheets 取出相應 cid 後再篩
// 客戶.
//
// 若 birthdate 的年份為 YearNone (使用者只輸入了月日, 如 "0825"), 改以「不分年,
// 只比月日」方式檢索, 並把結果按生日排序, 方便產生壽星名單.
func (s *SearchService) Search(c SearchCriteria) ([]domain.Customer, error) {
	filter := map[string]any{}
	if c.Name != "" {
		filter["name"] = map[string]any{"$regex": fmt.Sprintf(".*%s.*", c.Name)}
	}
	if c.Addr != "" {
		filter["addr"] = map[string]any{"$regex": fmt.Sprintf(".*%s.*", c.Addr)}
	}
	if c.Phone != "" {
		filter["phones"] = map[string]any{"$regex": fmt.Sprintf(".*%s.*", c.Phone)}
	}
	monthDayOnly := false
	if c.Birthdate != nil {
		if c.Birthdate.Year() == domain.YearNone {
			monthDayOnly = true
			filter["$expr"] = map[string]any{
				"$and": []any{
					map[string]any{"$eq": []any{
						map[string]any{"$month": "$birthdate"}, int(c.Birthdate.Month()),
					}},
					map[string]any{"$eq": []any{
						map[string]any{"$dayOfMonth": "$birthdate"}, c.Birthdate.Day(),
					}},
				},
			}
		} else {
			filter["birthdate"] = *c.Birthdate
		}
	}

	if c.DateField != "" && (c.DateFrom != nil || c.DateTo != nil) {
		var bsonField string
		switch c.DateField {
		case "order":
			bsonField = "order_time"
		case "deliver":
			bsonField = "deliver_time"
		default:
			return nil, fmt.Errorf("無效的日期欄位: %s", c.DateField)
		}
		// 將迄推到當日 23:59:59.999999999, 讓「3/15~3/15」涵蓋整天.
		var to *time.Time
		if c.DateTo != nil {
			t := c.DateTo.Add(24*time.Hour - time.Nanosecond)
			to = &t
		}
		ids, err := s.worksheets.DistinctCustomerIDsByDateRange(context.Background(), bsonField, c.DateFrom, to)
		if err != nil {
			return nil, err
		}
		if len(ids) == 0 {
			return []domain.Customer{}, nil
		}
		filter["_id"] = map[string]any{"$in": ids}
	}

	res, err := s.repo.Find(context.Background(), filter)
	if err != nil {
		return nil, err
	}
	if monthDayOnly {
		sort.SliceStable(res, func(i, j int) bool {
			bi, bj := res[i].Birthdate, res[j].Birthdate
			if bi == nil {
				return false
			}
			if bj == nil {
				return true
			}
			return bi.Before(*bj)
		})
	}
	return res, nil
}

// History 回傳目前 session 的搜尋歷史.
func (s *SearchService) History() ([]domain.Customer, error) {
	return s.history.List(context.Background())
}

// Remember 將客戶加入目前 session 的歷史中 (會去重).
func (s *SearchService) Remember(c domain.Customer) error {
	return s.history.Remember(context.Background(), c)
}

