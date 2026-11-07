package order

import (
	"context"
	"errors"
	"reflect"
	"testing"
)

var (
	errRegressionOperation = errors.New("operation failed")
	errRegressionRollback = errors.New("rollback failed")
)

type regressionDatabase struct {
	tx *regressionTransaction
}

func (db *regressionDatabase) Begin(context.Context) (Transaction, error) {
	return db.tx, nil
}

type regressionTransaction struct {
	events     []string
	createErr  error
	reserveErr error
	rollbackErr error
}

func (tx *regressionTransaction) CreateOrder(context.Context, Order) error {
	tx.events = append(tx.events, "create")
	return tx.createErr
}

func (tx *regressionTransaction) ReserveInventory(context.Context, string, int) error {
	tx.events = append(tx.events, "reserve")
	return tx.reserveErr
}

func (tx *regressionTransaction) Commit() error {
	tx.events = append(tx.events, "commit")
	return nil
}

func (tx *regressionTransaction) Rollback() error {
	tx.events = append(tx.events, "rollback")
	return tx.rollbackErr
}

func TestRegressionRollbackErrorDoesNotMaskOperationError(t *testing.T) {
	tx := &regressionTransaction{
		reserveErr:  errRegressionOperation,
		rollbackErr: errRegressionRollback,
	}
	service := NewOrderService(&regressionDatabase{tx: tx})

	err := service.PlaceOrder(context.Background(), Order{
		ID: "regression-1", SKU: "SKU-1", Quantity: 1,
	})

	if !errors.Is(err, errRegressionOperation) {
		t.Fatalf("PlaceOrder() error = %v, want original operation error", err)
	}
	if errors.Is(err, errRegressionRollback) {
		t.Fatalf("rollback error must not replace operation error: %v", err)
	}
	if !reflect.DeepEqual(tx.events, []string{"create", "reserve", "rollback"}) {
		t.Fatalf("transaction events = %v", tx.events)
	}
}

func TestRegressionSuccessfulOperationCommitsExactlyOnce(t *testing.T) {
	tx := &regressionTransaction{}
	service := NewOrderService(&regressionDatabase{tx: tx})

	if err := service.PlaceOrder(context.Background(), Order{
		ID: "regression-2", SKU: "SKU-2", Quantity: 3,
	}); err != nil {
		t.Fatalf("PlaceOrder() error = %v", err)
	}

	want := []string{"create", "reserve", "commit", "rollback"}
	if !reflect.DeepEqual(tx.events, want) {
		t.Fatalf("transaction events = %v, want %v", tx.events, want)
	}
}
