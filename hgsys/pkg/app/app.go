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

// Config bundles the CLI flags the bootstrap needs.
type Config struct {
	Host     string
	Port     int
	TestMode bool
	Debug    bool
	RepoRoot string
}

// Connect opens a Mongo connection using the host/port from cfg. Caller owns
// the returned client and should defer client.Disconnect.
func Connect(ctx context.Context, cfg Config) (*mongo.Client, error) {
	uri := fmt.Sprintf("mongodb://%s:%d", cfg.Host, cfg.Port)
	clientCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
	defer cancel()
	client, err := mongo.Connect(clientCtx, mongooptions.Client().ApplyURI(uri))
	if err != nil {
		return nil, fmt.Errorf("mongo connect %s: %w", uri, err)
	}
	if err := client.Ping(clientCtx, nil); err != nil {
		return nil, fmt.Errorf("mongo ping %s: %w", uri, err)
	}
	slog.Info("connected to MongoDB", "uri", uri)
	return client, nil
}

// PrepareRepositories wires the repositories on the given client and clears
// the search history (matches legacy startup behavior).
func PrepareRepositories(ctx context.Context, client *mongo.Client) (*repository.Repositories, error) {
	repos := repository.New(client)
	if err := repos.SearchHistory.Clear(ctx); err != nil {
		return nil, fmt.Errorf("clear search history: %w", err)
	}
	return repos, nil
}
