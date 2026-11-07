package order

import (
	"context"
	"errors"
	"testing"
)

var errInventoryUnavailable = errors.New("inventory unavailable")

type memoryDatabase struct {
	orders      []Order
	inventory   map[string]int
	failReserve bool
}

type memoryTransaction struct {
	db       *memoryDatabase
	order    *Order
	reserved map[string]int
	closed   bool
}

func newMemoryDatabase() *memoryDatabase {
	return &memoryDatabase{
		inventory: make(map[string]int),
	}
}

func (db *memoryDatabase) Begin(
	ctx context.Context,
) (Transaction, error) {
	if err := ctx.Err(); err != nil {
		return nil, err
	}

	return &memoryTransaction{
		db:       db,
		reserved: make(map[string]int),
	}, nil
}

func (tx *memoryTransaction) CreateOrder(
	ctx context.Context,
	order Order,
) error {
	if tx.closed {
		return ErrTransactionClosed
	}

	if err := ctx.Err(); err != nil {
		return err
	}

	copy := order
	tx.order = &copy
	return nil
}

func (tx *memoryTransaction) ReserveInventory(
	ctx context.Context,
	sku string,
	quantity int,
) error {
	if tx.closed {
		return ErrTransactionClosed
	}

	if err := ctx.Err(); err != nil {
		return err
	}

	if tx.db.failReserve {
		return errInventoryUnavailable
	}

	tx.reserved[sku] += quantity
	return nil
}

func (tx *memoryTransaction) Commit() error {
	if tx.closed {
		return ErrTransactionClosed
	}

	if tx.order != nil {
		tx.db.orders = append(tx.db.orders, *tx.order)
	}

	for sku, quantity := range tx.reserved {
		tx.db.inventory[sku] += quantity
	}

	tx.closed = true
	return nil
}

func (tx *memoryTransaction) Rollback() error {
	if tx.closed {
		return nil
	}

	tx.order = nil
	tx.reserved = make(map[string]int)
	tx.closed = true

	return nil
}

func TestPlaceOrderCommitsAllOperations(t *testing.T) {
	db := newMemoryDatabase()
	service := NewOrderService(db)

	order := Order{
		ID:       "order-001",
		SKU:      "SKU-001",
		Quantity: 3,
	}

	err := service.PlaceOrder(context.Background(), order)
	if err != nil {
		t.Fatalf("PlaceOrder() error = %v", err)
	}

	if len(db.orders) != 1 {
		t.Fatalf("expected 1 persisted order, got %d", len(db.orders))
	}

	if db.inventory["SKU-001"] != 3 {
		t.Fatalf(
			"expected inventory reservation of 3, got %d",
			db.inventory["SKU-001"],
		)
	}
}

func TestPlaceOrderRollsBackOnInventoryFailure(t *testing.T) {
	db := newMemoryDatabase()
	db.failReserve = true

	service := NewOrderService(db)

	order := Order{
		ID:       "order-002",
		SKU:      "SKU-002",
		Quantity: 5,
	}

	err := service.PlaceOrder(context.Background(), order)
	if !errors.Is(err, errInventoryUnavailable) {
		t.Fatalf("expected inventory error, got %v", err)
	}

	if len(db.orders) != 0 {
		t.Fatalf(
			"expected no persisted orders after rollback, got %d",
			len(db.orders),
		)
	}

	if db.inventory["SKU-002"] != 0 {
		t.Fatalf(
			"expected inventory unchanged, got %d",
			db.inventory["SKU-002"],
		)
	}
}
