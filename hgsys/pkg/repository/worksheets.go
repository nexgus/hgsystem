package repository

import (
	"context"
	"time"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"

	"hgsys/pkg/domain"
)

// WorksheetRepository 封裝 `worksheets` collection 的 CRUD 操作.
type WorksheetRepository struct {
	coll *mongo.Collection
}

func NewWorksheetRepository(db *mongo.Database) *WorksheetRepository {
	return &WorksheetRepository{coll: db.Collection("worksheets")}
}

// FindForCustomer 回傳 cid 所對應客戶之所有 worksheet.
func (r *WorksheetRepository) FindForCustomer(ctx context.Context, cid string) ([]domain.Worksheet, error) {
	cur, err := r.coll.Find(ctx, bson.M{"cid": cid})
	if err != nil {
		return nil, err
	}
	defer cur.Close(ctx)
	var out []domain.Worksheet
	if err := cur.All(ctx, &out); err != nil {
		return nil, err
	}
	return out, nil
}

// Insert 儲存 `w`; 若 ID 為空, 會自動指派新的字串化 ObjectId.
func (r *WorksheetRepository) Insert(ctx context.Context, w *domain.Worksheet) (string, error) {
	if w.ID == "" {
		w.ID = newID()
	}
	if _, err := r.coll.InsertOne(ctx, w); err != nil {
		return "", err
	}
	return w.ID, nil
}

// Replace 以 `w` 覆寫 `id` 對應的 worksheet (ID 保留不變).
func (r *WorksheetRepository) Replace(ctx context.Context, id string, w domain.Worksheet) error {
	w.ID = ""
	_, err := r.coll.ReplaceOne(ctx, bson.M{"_id": id}, w)
	return err
}

// Delete 依 id 刪除單筆 worksheet; 回傳被刪除的筆數 (0 或 1).
func (r *WorksheetRepository) Delete(ctx context.Context, id string) (int64, error) {
	res, err := r.coll.DeleteOne(ctx, bson.M{"_id": id})
	if err != nil {
		return 0, err
	}
	return res.DeletedCount, nil
}

// DistinctCustomerIDsByDateRange 回傳在指定期間內有 worksheet 之 cid 去重集合.
// field 為 bson tag, 預期為 "order_time" 或 "deliver_time".
// from / to 為 nil 代表該端不限. caller 應保證至少一端非 nil, 否則回傳的是
// 所有「該欄位有值」的 cid (近似全表), 通常無意義.
func (r *WorksheetRepository) DistinctCustomerIDsByDateRange(ctx context.Context, field string, from, to *time.Time) ([]string, error) {
	rangeCond := bson.M{}
	if from != nil {
		rangeCond["$gte"] = *from
	}
	if to != nil {
		rangeCond["$lte"] = *to
	}
	vals, err := r.coll.Distinct(ctx, "cid", bson.M{field: rangeCond})
	if err != nil {
		return nil, err
	}
	out := make([]string, 0, len(vals))
	for _, v := range vals {
		if s, ok := v.(string); ok {
			out = append(out, s)
		}
	}
	return out, nil
}

// DeleteForCustomer 串聯刪除 cid 所屬之所有 worksheet.
func (r *WorksheetRepository) DeleteForCustomer(ctx context.Context, cid string) (int64, error) {
	res, err := r.coll.DeleteMany(ctx, bson.M{"cid": cid})
	if err != nil {
		return 0, err
	}
	return res.DeletedCount, nil
}
