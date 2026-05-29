// Package repository 實作對舊有 hgsystem collection 之 MongoDB 後端存取.
// DB 名稱與文件結構皆固定不變, 以與 live production 資料及既有 mongodump 備份
// 相容.
package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
)

// DatabaseName 為舊有 Mongo DB 名稱, 不可變動 — mongodump 產生的備份中內嵌此
// 名稱.
const DatabaseName = "hgsystem"

// Repositories 將各 collection 的 repository 打包在一起, 讓 bootstrap 能以
// 單一值交給 app layer 使用.
type Repositories struct {
	Customers *CustomerRepository
	Worksheets *WorksheetRepository
	SearchHistory *SearchHistoryRepository
	Titles *TitleRepository
}

// New 於指定的 client 上開啟 hgsystem 資料庫, 回傳打包好的 repositories.
func New(client *mongo.Client) *Repositories {
	db := client.Database(DatabaseName)
	return &Repositories{
		Customers:     NewCustomerRepository(db),
		Worksheets:    NewWorksheetRepository(db),
		SearchHistory: NewSearchHistoryRepository(db),
		Titles:        NewTitleRepository(db),
	}
}

// newID 回傳新的字串化 ObjectId, 符合舊有慣例 — `_id` 以字串存放, 而非原生
// ObjectId.
func newID() string {
	return primitive.NewObjectID().Hex()
}

// ctx 回傳一個 background context. 若 caller 需要 cancellation, 應自行將 context
// 傳入 repository 方法.
func ctx() context.Context {
	return context.Background()
}
