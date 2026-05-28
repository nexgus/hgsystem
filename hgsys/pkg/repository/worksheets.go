package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"

	"hgsys/pkg/domain"
)

// WorksheetRepository wraps CRUD on the `worksheets` collection.
type WorksheetRepository struct {
	coll *mongo.Collection
}

func NewWorksheetRepository(db *mongo.Database) *WorksheetRepository {
	return &WorksheetRepository{coll: db.Collection("worksheets")}
}

// FindForCustomer returns all worksheets belonging to the customer with cid.
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

// Insert stores `w`, auto-assigning a new stringified ObjectId if ID is empty.
func (r *WorksheetRepository) Insert(ctx context.Context, w *domain.Worksheet) (string, error) {
	if w.ID == "" {
		w.ID = newID()
	}
	if _, err := r.coll.InsertOne(ctx, w); err != nil {
		return "", err
	}
	return w.ID, nil
}

// Replace overwrites the worksheet at `id` with `w` (ID is preserved).
func (r *WorksheetRepository) Replace(ctx context.Context, id string, w domain.Worksheet) error {
	w.ID = ""
	_, err := r.coll.ReplaceOne(ctx, bson.M{"_id": id}, w)
	return err
}

// Delete removes a single worksheet by id; returns deleted count (0 or 1).
func (r *WorksheetRepository) Delete(ctx context.Context, id string) (int64, error) {
	res, err := r.coll.DeleteOne(ctx, bson.M{"_id": id})
	if err != nil {
		return 0, err
	}
	return res.DeletedCount, nil
}

// DeleteForCustomer cascades deletion of all worksheets owned by cid.
func (r *WorksheetRepository) DeleteForCustomer(ctx context.Context, cid string) (int64, error) {
	res, err := r.coll.DeleteMany(ctx, bson.M{"cid": cid})
	if err != nil {
		return 0, err
	}
	return res.DeletedCount, nil
}
