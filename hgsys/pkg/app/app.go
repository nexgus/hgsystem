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
// (對齊舊版啟動行為). 另外於首次啟動時 seed 預設稱謂清單 (titles collection
// 為空時才會寫入, 不會覆寫使用者自訂的內容).
func PrepareRepositories(ctx context.Context, client *mongo.Client) (*repository.Repositories, error) {
	repos := repository.New(client)
	if err := repos.SearchHistory.Clear(ctx); err != nil {
		return nil, fmt.Errorf("clear search history: %w", err)
	}
	if err := repos.Titles.SeedIfEmpty(ctx, DefaultTitles); err != nil {
		return nil, fmt.Errorf("seed titles: %w", err)
	}
	return repos, nil
}

// DefaultTitles 為首次啟動 titles collection 時寫入的預設稱謂. 空字串不在此列 —
// 它由前端視為「無稱謂」的固定選項, 而非清單成員.
var DefaultTitles = []string{
	"Miss",
	"Mr.",
	"先生",
	"太太",
	"女士",
	"婆婆",
	"小姐",
	"小弟",
	"居士",
	"師父",
	"法師",
}
