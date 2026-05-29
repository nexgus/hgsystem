package repository

import (
	"context"
	"errors"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"

	"hgsys/pkg/domain"
)

// SearchHistoryRepository 封裝 `search` collection, 該 collection 記錄使用者
// 在目前 session 中檢視過的客戶.
//
// 此 collection 於每次啟動時清空; 被選取的客戶會被追加進去 (依 _id 去重),
// 讓使用者可透過搜尋對話框的「歷史」按鈕重新開啟.
type SearchHistoryRepository struct {
	coll *mongo.Collection
}

func NewSearchHistoryRepository(db *mongo.Database) *SearchHistoryRepository {
	return &SearchHistoryRepository{coll: db.Collection("search")}
}

// Clear 清除歷史; 於啟動時呼叫一次.
func (r *SearchHistoryRepository) Clear(ctx context.Context) error {
	_, err := r.coll.DeleteMany(ctx, bson.M{})
	return err
}

// List 以 customer slice 形式回傳目前的歷史.
func (r *SearchHistoryRepository) List(ctx context.Context) ([]domain.Customer, error) {
	cur, err := r.coll.Find(ctx, bson.M{})
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

// Remember 若該客戶不存在於歷史中則加入 (依 _id 去重).
func (r *SearchHistoryRepository) Remember(ctx context.Context, c domain.Customer) error {
	err := r.coll.FindOne(ctx, bson.M{"_id": c.ID}).Err()
	if err == nil {
		return nil // 已存在
	}
	if !errors.Is(err, mongo.ErrNoDocuments) {
		return err
	}
	_, err = r.coll.InsertOne(ctx, c)
	return err
}
