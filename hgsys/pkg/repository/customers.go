package repository

import (
	"context"
	"errors"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/mongo"

	"hgsys/pkg/domain"
)

// CustomerRepository wraps CRUD on the `customers` collection.
type CustomerRepository struct {
	coll *mongo.Collection
}

func NewCustomerRepository(db *mongo.Database) *CustomerRepository {
	return &CustomerRepository{coll: db.Collection("customers")}
}

// Count returns the total customer count.
func (r *CustomerRepository) Count(ctx context.Context) (int64, error) {
	return r.coll.CountDocuments(ctx, bson.M{})
}

// Find returns all customers matching `filter` (use bson.M{} for all).
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

// Get returns the customer with the given id, or nil if not found.
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

// Insert stores `c`, auto-assigning a new stringified ObjectId if ID is empty.
// Returns the stored id.
func (r *CustomerRepository) Insert(ctx context.Context, c *domain.Customer) (string, error) {
	if c.ID == "" {
		c.ID = newID()
	}
	if _, err := r.coll.InsertOne(ctx, c); err != nil {
		return "", err
	}
	return c.ID, nil
}

// Replace overwrites the customer at `id` with `c` (ID itself is preserved).
func (r *CustomerRepository) Replace(ctx context.Context, id string, c domain.Customer) error {
	c.ID = ""
	_, err := r.coll.ReplaceOne(ctx, bson.M{"_id": id}, c)
	return err
}

// Delete removes the customer with the given id. Worksheets are NOT cascaded;
// the caller is responsible (typically WorksheetRepository.DeleteForCustomer).
func (r *CustomerRepository) Delete(ctx context.Context, id string) error {
	_, err := r.coll.DeleteOne(ctx, bson.M{"_id": id})
	return err
}
