package app

import (
	"context"
	"fmt"
	"log/slog"
	"time"

	"go.mongodb.org/mongo-driver/mongo"
	mongooptions "go.mongodb.org/mongo-driver/mongo/options"

	"hgsys/pkg/repository"
)

// Config 把 bootstrap 需要用到的 CLI 旗標包成一個結構.
type Config struct {
	Host     string
	Port     int
	NoDB     bool
	TestMode bool
	Debug    bool
	RepoRoot string
}

// Connect 依 cfg 的 host / port 開啟 Mongo 連線. 回傳的 client 由 caller 持有,
// 應自行 defer client.Disconnect.
//
// 當 Ping 失敗 (server 無法連線) 時, *client 仍會與 error 一同回傳, 讓 caller
// 可選擇以 GUI-only 模式繼續執行 — 資料操作會在呼叫時失敗, 但 UI 仍可載入.
//
// 若 cfg.NoDB 為 true, 則完全略過 Ping (避免 5 秒 timeout), 直接回傳 client.
// 後續任何 Mongo 操作仍會在呼叫時嘗試連線並失敗, 適合純檢視 GUI 的情境.
func Connect(ctx context.Context, cfg Config) (*mongo.Client, error) {
	uri := fmt.Sprintf("mongodb://%s:%d", cfg.Host, cfg.Port)
	clientCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	client, err := mongo.Connect(clientCtx, mongooptions.Client().ApplyURI(uri))
	if err != nil {
		return nil, fmt.Errorf("mongo connect %s: %w", uri, err)
	}
	if cfg.NoDB {
		slog.Info("已指定 --nodb, 略過 MongoDB ping", "uri", uri)
		return client, nil
	}
	if err := client.Ping(clientCtx, nil); err != nil {
		return client, fmt.Errorf("mongo ping %s: %w", uri, err)
	}
	slog.Info("已連線到 MongoDB", "uri", uri)
	return client, nil
}

// PrepareRepositories 於指定的 client 上建立各 repository, 並清空搜尋歷史
// (對齊舊版啟動行為).
func PrepareRepositories(ctx context.Context, client *mongo.Client) (*repository.Repositories, error) {
	repos := repository.New(client)
	if err := repos.SearchHistory.Clear(ctx); err != nil {
		return nil, fmt.Errorf("clear search history: %w", err)
	}
	return repos, nil
}
