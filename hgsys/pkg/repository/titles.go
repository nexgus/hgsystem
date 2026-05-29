package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"
	"go.mongodb.org/mongo-driver/mongo/options"
)

// TitleRepository 封裝 `titles` collection. 每筆 document 形如 `{_id: "<稱謂>"}`,
// 整個清單就是這個 collection 內所有 _id.
//
// 空字串 ("無稱謂") 不存入此 collection, 由前端視為預設值. 髒資料 (歷史 customer
// 中不合法的 title) 亦不放入; 它們留在原本的 customer 文件裡照常顯示.
type TitleRepository struct {
	coll *mongo.Collection
}

func NewTitleRepository(db *mongo.Database) *TitleRepository {
	return &TitleRepository{coll: db.Collection("titles")}
}

// List 以 string slice 回傳目前已登錄的稱謂. Mongo 預設依插入順序回傳, 不另做排序.
func (r *TitleRepository) List(ctx context.Context) ([]string, error) {
	cur, err := r.coll.Find(ctx, bson.M{})
	if err != nil {
		return nil, err
	}
	defer cur.Close(ctx)
	var docs []struct {
		ID string `bson:"_id"`
	}
	if err := cur.All(ctx, &docs); err != nil {
		return nil, err
	}
	out := make([]string, 0, len(docs))
	for _, d := range docs {
		out = append(out, d.ID)
	}
	return out, nil
}

// Add 寫入新稱謂; 已存在則為 no-op.
func (r *TitleRepository) Add(ctx context.Context, name string) error {
	if name == "" {
		return nil
	}
	_, err := r.coll.UpdateOne(
		ctx,
		bson.M{"_id": name},
		bson.M{"$setOnInsert": bson.M{"_id": name}},
		options.Update().SetUpsert(true),
	)
	return err
}

// Remove 移除指定稱謂; 不存在則為 no-op.
func (r *TitleRepository) Remove(ctx context.Context, name string) error {
	if name == "" {
		return nil
	}
	_, err := r.coll.DeleteOne(ctx, bson.M{"_id": name})
	return err
}

// SeedIfEmpty 若 collection 為空則寫入 defaults. 用於首次啟動時自動建立預設清單.
// 已有任何資料時 (使用者已自訂過) 完全不動.
func (r *TitleRepository) SeedIfEmpty(ctx context.Context, defaults []string) error {
	n, err := r.coll.CountDocuments(ctx, bson.M{})
	if err != nil {
		return err
	}
	if n > 0 {
		return nil
	}
	docs := make([]any, 0, len(defaults))
	for _, name := range defaults {
		if name == "" {
			continue
		}
		docs = append(docs, bson.M{"_id": name})
	}
	if len(docs) == 0 {
		return nil
	}
	_, err = r.coll.InsertMany(ctx, docs)
	return err
}
