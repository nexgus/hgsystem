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

// SearchResult 為搜尋 / 搜尋紀錄回傳的單筆結果: 客戶本體, 外加其"最後一筆"
// worksheet 中要在搜尋清單直接呈現的欄位 (右眼 / 左眼度數與收 / 交件日).
// 客戶無任何 worksheet 時, 度數為空字串, 日期為 nil.
type SearchResult struct {
	Customer        domain.Customer `json:"customer"`
	LastSphR        string          `json:"lastSphR"`
	LastSphL        string          `json:"lastSphL"`
	LastOrderTime   *time.Time      `json:"lastOrderTime"`
	LastDeliverTime *time.Time      `json:"lastDeliverTime"`
}

// withLatestWorksheets 為 customers 各補上其最後一筆 worksheet 的摘要欄位, 組成
// []SearchResult. 以單次 aggregation 取所有相關 worksheet, 避免逐一查詢.
//
// field / from / to 對應搜尋的日期範圍條件 (field 為 "order_time" /
// "deliver_time"); 有帶時, 取的是該日期範圍內的最後一筆工單, 而非全域最後一筆.
// field 為空時取全域 (以收件日) 最後一筆.
func (s *SearchService) withLatestWorksheets(ctx context.Context, customers []domain.Customer, field string, from, to *time.Time) ([]SearchResult, error) {
	cids := make([]string, 0, len(customers))
	for _, c := range customers {
		cids = append(cids, c.ID)
	}
	latest, err := s.worksheets.LatestForCustomers(ctx, cids, field, from, to)
	if err != nil {
		return nil, err
	}
	out := make([]SearchResult, 0, len(customers))
	for _, c := range customers {
		r := SearchResult{Customer: c}
		if w, ok := latest[c.ID]; ok {
			r.LastSphR = w.SphR
			r.LastSphL = w.SphL
			r.LastOrderTime = w.OrderTime
			r.LastDeliverTime = w.DeliverTime
		}
		out = append(out, r)
	}
	return out, nil
}

// Search 以子字串 regex 比對 name / addr / phone, 並以精確比對檢索 birthdate.
// 空欄位會被忽略. 若指定了工作單期間條件, 會跨 worksheets 取出相應 cid 後再篩
// 客戶.
//
// 若 birthdate 的年份為 YearNone (使用者只輸入了月日, 如 "0825"), 改以"不分年,
// 只比月日"方式檢索, 並把結果按生日排序, 方便產生壽星名單.
func (s *SearchService) Search(c SearchCriteria) ([]SearchResult, error) {
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

	// wsField / wsFrom / wsTo 記錄工單日期範圍條件, 一併用於後續"取範圍內最後一筆
	// 工單"; wsField 為空代表未指定日期範圍.
	var wsField string
	var wsFrom, wsTo *time.Time
	if c.DateField != "" && (c.DateFrom != nil || c.DateTo != nil) {
		switch c.DateField {
		case "order":
			wsField = "order_time"
		case "deliver":
			wsField = "deliver_time"
		default:
			return nil, fmt.Errorf("無效的日期欄位: %s", c.DateField)
		}
		wsFrom = c.DateFrom
		// 將迄推到當日 23:59:59.999999999, 讓"3/15~3/15"涵蓋整天.
		if c.DateTo != nil {
			t := c.DateTo.Add(24*time.Hour - time.Nanosecond)
			wsTo = &t
		}
		ids, err := s.worksheets.DistinctCustomerIDsByDateRange(context.Background(), wsField, wsFrom, wsTo)
		if err != nil {
			return nil, err
		}
		if len(ids) == 0 {
			return []SearchResult{}, nil
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
	return s.withLatestWorksheets(context.Background(), res, wsField, wsFrom, wsTo)
}

// History 回傳目前 session 的搜尋歷史.
func (s *SearchService) History() ([]SearchResult, error) {
	list, err := s.history.List(context.Background())
	if err != nil {
		return nil, err
	}
	return s.withLatestWorksheets(context.Background(), list, "", nil, nil)
}

// Remember 將客戶加入目前 session 的歷史中 (會去重).
func (s *SearchService) Remember(c domain.Customer) error {
	return s.history.Remember(context.Background(), c)
}

