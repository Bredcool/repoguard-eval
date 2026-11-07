package order

import (
	"context"
	"errors"
	"reflect"
	"testing"
)

var (
	errHiddenBegin  = errors.New("begin failed")
	errHiddenCreate = errors.New("create order failed")
	errHiddenReserve = errors.New("reserve inventory failed")
	errHiddenCommit = errors.New("commit failed")
)

type hiddenDatabase struct {
	tx       *hiddenTransaction
	beginErr error
}

func (db *hiddenDatabase) Begin(context.Context) (Transaction, error) {
	if db.beginErr != nil {
		return nil, db.beginErr
	}
	db.tx = &hiddenTransaction{}
	return db.tx, nil
}

type hiddenTransaction struct {
	events       []string
	createErr    error
	reserveErr   error
	commitErr    error
	rollbackErr  error
	closed       bool
	commits      int
	rollbacks    int
	persisted    bool
}

func (tx *hiddenTransaction) CreateOrder(context.Context, Order) error {
	tx.events = append(tx.events, "create")
	if tx.closed {
		return ErrTransactionClosed
	}
	return tx.createErr
}

func (tx *hiddenTransaction) ReserveInventory(context.Context, string, int) error {
	tx.events = append(tx.events, "reserve")
	if tx.closed {
		return ErrTransactionClosed
	}
	return tx.reserveErr
}

func (tx *hiddenTransaction) Commit() error {
	tx.events = append(tx.events, "commit")
	tx.commits++
	if tx.closed {
		return ErrTransactionClosed
	}
	if tx.commitErr != nil {
		return tx.commitErr
	}
	tx.persisted = true
	tx.closed = true
	return nil
}

func (tx *hiddenTransaction) Rollback() error {
	tx.events = append(tx.events, "rollback")
	tx.rollbacks++
	if tx.closed {
		return nil
	}
	tx.persisted = false
	tx.closed = true
	return tx.rollbackErr
}

func TestHiddenPlaceOrderBeginsTransactionBeforeOperations(t *testing.T) {
	db := &hiddenDatabase{}
	service := NewOrderService(db)

	err := service.PlaceOrder(context.Background(), Order{
		ID: "hidden-1", SKU: "SKU-1", Quantity: 2,
	})
	if err != nil {
		t.Fatalf("PlaceOrder() error = %v", err)
	}

	want := []string{"create", "reserve", "commit", "rollback"}
	if !reflect.DeepEqual(db.tx.events, want) {
		t.Fatalf("transaction events = %v, want %v", db.tx.events, want)
	}
	if db.tx.commits != 1 {
		t.Fatalf("commit count = %d, want 1", db.tx.commits)
	}
	if !db.tx.persisted {
		t.Fatal("successful transaction was not persisted")
	}
}

func TestHiddenPlaceOrderPropagatesBeginError(t *testing.T) {
	db := &hiddenDatabase{beginErr: errHiddenBegin}
	service := NewOrderService(db)

	err := service.PlaceOrder(context.Background(), Order{})
	if !errors.Is(err, errHiddenBegin) {
		t.Fatalf("PlaceOrder() error = %v, want %v", err, errHiddenBegin)
	}
	if db.tx != nil {
		t.Fatal("transaction should not be created after begin failure")
	}
}

func TestHiddenPlaceOrderRollsBackWhenCreateFails(t *testing.T) {
	db := &hiddenDatabase{}
	service := NewOrderService(db)
	db.tx = &hiddenTransaction{createErr: errHiddenCreate}

	dbWithTransaction := &hiddenDatabaseWithExistingTransaction{tx: db.tx}
	service = NewOrderService(dbWithTransaction)

	err := service.PlaceOrder(context.Background(), Order{})
	if !errors.Is(err, errHiddenCreate) {
		t.Fatalf("PlaceOrder() error = %v, want %v", err, errHiddenCreate)
	}
	if db.tx.commits != 0 || db.tx.rollbacks != 1 {
		t.Fatalf("commits = %d, rollbacks = %d; want 0 and 1",
			db.tx.commits, db.tx.rollbacks)
	}
	if db.tx.persisted {
		t.Fatal("failed operation must not persist data")
	}
}

type hiddenDatabaseWithExistingTransaction struct {
	tx *hiddenTransaction
}

func (db *hiddenDatabaseWithExistingTransaction) Begin(context.Context) (Transaction, error) {
	return db.tx, nil
}

func TestHiddenPlaceOrderRollsBackWhenReserveFails(t *testing.T) {
	tx := &hiddenTransaction{reserveErr: errHiddenReserve}
	service := NewOrderService(&hiddenDatabaseWithExistingTransaction{tx: tx})

	err := service.PlaceOrder(context.Background(), Order{})
	if !errors.Is(err, errHiddenReserve) {
		t.Fatalf("PlaceOrder() error = %v, want %v", err, errHiddenReserve)
	}
	if tx.commits != 0 || tx.rollbacks != 1 {
		t.Fatalf("commits = %d, rollbacks = %d; want 0 and 1",
			tx.commits, tx.rollbacks)
	}
	if tx.persisted {
		t.Fatal("failed operation must not persist data")
	}
}

func TestHiddenPlaceOrderPropagatesCommitError(t *testing.T) {
	tx := &hiddenTransaction{commitErr: errHiddenCommit}
	service := NewOrderService(&hiddenDatabaseWithExistingTransaction{tx: tx})

	err := service.PlaceOrder(context.Background(), Order{})
	if !errors.Is(err, errHiddenCommit) {
		t.Fatalf("PlaceOrder() error = %v, want %v", err, errHiddenCommit)
	}
	if tx.commits != 1 || tx.rollbacks != 1 {
		t.Fatalf("commits = %d, rollbacks = %d; want 1 and 1",
			tx.commits, tx.rollbacks)
	}
	if tx.persisted {
		t.Fatal("commit failure must not persist data")
	}
}
