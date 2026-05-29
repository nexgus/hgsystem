package repository

import (
	"context"
	"errors"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"

	"hgsys/pkg/domain"
)

// CustomerRepository 封裝 `customers` collection 的 CRUD 操作.
type CustomerRepository struct {
	coll *mongo.Collection
}

func NewCustomerRepository(db *mongo.Database) *CustomerRepository {
	return &CustomerRepository{coll: db.Collection("customers")}
}

// Count 回傳客戶總數.
func (r *CustomerRepository) Count(ctx context.Context) (int64, error) {
	return r.coll.CountDocuments(ctx, bson.M{})
}

// Find 回傳所有符合 `filter` 的客戶 (要取全部時可傳 bson.M{}).
func (r *CustomerRepository) Find(ctx context.Context, filter bson.M) ([]domain.Customer, error) {
	if filter == nil {
		filter = bson.M{}
	}
	cur, err := r.coll.Find(ctx, filter)
	if err != nil {
		return nil, err
	}
	defer cur.Close(ctx)
	var out []domain.Customer
	if err := cur.All(ctx, &out); err != nil {
		return nil, err
	}
	return out, nil
}

// Get 回傳指定 id 的客戶, 找不到時回傳 nil.
func (r *CustomerRepository) Get(ctx context.Context, id string) (*domain.Customer, error) {
	var c domain.Customer
	err := r.coll.FindOne(ctx, bson.M{"_id": id}).Decode(&c)
	if errors.Is(err, mongo.ErrNoDocuments) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	return &c, nil
}

// Insert 儲存 `c`; 若 ID 為空, 會自動指派新的字串化 ObjectId. 回傳儲存後的 id.
func (r *CustomerRepository) Insert(ctx context.Context, c *domain.Customer) (string, error) {
	if c.ID == "" {
		c.ID = newID()
	}
	if _, err := r.coll.InsertOne(ctx, c); err != nil {
		return "", err
	}
	return c.ID, nil
}

// Replace 以 `c` 覆寫 `id` 對應的客戶 (ID 本身保留不變).
func (r *CustomerRepository) Replace(ctx context.Context, id string, c domain.Customer) error {
	c.ID = ""
	_, err := r.coll.ReplaceOne(ctx, bson.M{"_id": id}, c)
	return err
}

// Delete 刪除指定 id 的客戶. 不會串聯刪除 worksheet; 串聯刪除由 caller 自行負責
// (通常為 WorksheetRepository.DeleteForCustomer).
func (r *CustomerRepository) Delete(ctx context.Context, id string) error {
	_, err := r.coll.DeleteOne(ctx, bson.M{"_id": id})
	return err
}
