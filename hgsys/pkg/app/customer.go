// Package app contains the Wails service bindings exposed to the Vue frontend.
//
// Each *Service type holds repository / coordinator references and exposes a
// thin set of methods callable from JS via wails3 generate bindings. Methods
// return plain values (no Mongo / Wails types) so the generated TS API stays
// readable.
package app

import (
	"context"
	"errors"
	"fmt"
	"time"

	"hgsys/pkg/domain"
	"hgsys/pkg/repository"
)

// CustomerService binds the customer CRUD methods. Coordination state
// (current selection, edit mode) lives entirely on the frontend store —
// Go just returns data and persists changes.
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

// Count returns the total customer count.
func (s *CustomerService) Count() (int64, error) {
	return s.repo.Count(context.Background())
}

// Get returns the customer with id, or an error if not found.
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

// Insert persists a new customer (id auto-generated when empty).
func (s *CustomerService) Insert(c domain.Customer) (string, error) {
	if c.Name == "" {
		return "", errors.New("姓名不得為空白")
	}
	return s.repo.Insert(context.Background(), &c)
}

// Update overwrites the customer at id with the supplied values.
func (s *CustomerService) Update(id string, c domain.Customer) error {
	if c.Name == "" {
		return errors.New("姓名不得為空白")
	}
	return s.repo.Replace(context.Background(), id, c)
}

// Delete removes the customer and cascades worksheet deletion. Returns the
// number of worksheets deleted along with the customer.
func (s *CustomerService) Delete(id string) (int64, error) {
	if err := s.repo.Delete(context.Background(), id); err != nil {
		return 0, err
	}
	return s.worksheets.DeleteForCustomer(context.Background(), id)
}

// SearchService is split out so the search dialog can have its own binding.
type SearchService struct {
	repo    *repository.CustomerRepository
	history *repository.SearchHistoryRepository
}

func NewSearchService(r *repository.Repositories) *SearchService {
	return &SearchService{repo: r.Customers, history: r.SearchHistory}
}

// SearchCriteria mirrors the legacy search dialog inputs.
type SearchCriteria struct {
	Name      string     `json:"name"`
	Addr      string     `json:"addr"`
	Phone     string     `json:"phone"`
	Birthdate *time.Time `json:"birthdate"`
}

// Search runs a regex-on-substring lookup over name/addr/phone plus an exact
// match on birthdate. Empty fields are ignored.
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
	if c.Birthdate != nil {
		filter["birthdate"] = *c.Birthdate
	}
	return s.repo.Find(context.Background(), filter)
}

// History returns the current session's search history.
func (s *SearchService) History() ([]domain.Customer, error) {
	return s.history.List(context.Background())
}

// Remember adds a customer to the current session's history (deduped).
func (s *SearchService) Remember(c domain.Customer) error {
	return s.history.Remember(context.Background(), c)
}

