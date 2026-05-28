// Package repository implements MongoDB-backed access to the legacy hgsystem
// collections. The DB name and document shapes are pinned to stay compatible
// with live production data and existing mongodump backups.
package repository

import (
	"context"

	"go.mongodb.org/mongo-driver/bson/primitive"
	"go.mongodb.org/mongo-driver/mongo"
)

// DatabaseName is the legacy Mongo DB name and MUST NOT change — backups
// produced by mongodump embed it.
const DatabaseName = "hgsystem"

// Repositories bundles the per-collection repositories so the bootstrap can
// hand them out to the app layer with a single value.
type Repositories struct {
	Customers *CustomerRepository
	Worksheets *WorksheetRepository
	SearchHistory *SearchHistoryRepository
}

// New opens the hgsystem database on the provided client and returns the
// bundled repositories.
func New(client *mongo.Client) *Repositories {
	db := client.Database(DatabaseName)
	return &Repositories{
		Customers:     NewCustomerRepository(db),
		Worksheets:    NewWorksheetRepository(db),
		SearchHistory: NewSearchHistoryRepository(db),
	}
}

// newID returns a fresh stringified ObjectId, matching the legacy convention
// of storing `_id` as a string rather than a native ObjectId.
func newID() string {
	return primitive.NewObjectID().Hex()
}

// ctx returns a background context. Callers that need cancellation should pass
// their own context to repository methods.
func ctx() context.Context {
	return context.Background()
}
