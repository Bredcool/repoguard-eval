package order

import (
	"context"
	"errors"
)

var ErrTransactionClosed = errors.New("transaction is closed")

type Order struct {
	ID       string
	SKU      string
	Quantity int
}

type Transaction interface {
	CreateOrder(ctx context.Context, order Order) error
	ReserveInventory(ctx context.Context, sku string, quantity int) error
	Commit() error
	Rollback() error
}

type Database interface {
	Begin(ctx context.Context) (Transaction, error)
}

type OrderService struct {
	db Database
}

func NewOrderService(db Database) *OrderService {
	return &OrderService{db: db}
}

func (s *OrderService) PlaceOrder(
	ctx context.Context,
	order Order,
) error {
	tx, err := s.db.Begin(ctx)
	if err != nil {
		return err
	}

	defer tx.Rollback()

	if err := tx.CreateOrder(ctx, order); err != nil {
		return err
	}

	// BUG: The transaction commits before inventory reservation.
	if err := tx.Commit(); err != nil {
		return err
	}

	if err := tx.ReserveInventory(
		ctx,
		order.SKU,
		order.Quantity,
	); err != nil {
		return err
	}

	return tx.Commit()
}
