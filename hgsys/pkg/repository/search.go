package repository

import (
	"context"
	"errors"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"

	"hgsys/pkg/domain"
)

// SearchHistoryRepository wraps the `search` collection, which records the
// customers the user has looked at during the current session.
//
// The collection is cleared on every startup; selected customers are appended
// (deduped by _id) so the user can re-open them via the search dialog's
// "history" button.
type SearchHistoryRepository struct {
	coll *mongo.Collection
}

func NewSearchHistoryRepository(db *mongo.Database) *SearchHistoryRepository {
	return &SearchHistoryRepository{coll: db.Collection("search")}
}

// Clear wipes the history; call once at startup.
func (r *SearchHistoryRepository) Clear(ctx context.Context) error {
	_, err := r.coll.DeleteMany(ctx, bson.M{})
	return err
}

// List returns the current history as a slice of customers.
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

// Remember inserts a customer into the history if absent (deduped by _id).
func (r *SearchHistoryRepository) Remember(ctx context.Context, c domain.Customer) error {
	err := r.coll.FindOne(ctx, bson.M{"_id": c.ID}).Err()
	if err == nil {
		return nil // already present
	}
	if !errors.Is(err, mongo.ErrNoDocuments) {
		return err
	}
	_, err = r.coll.InsertOne(ctx, c)
	return err
}
