package order

import (
	"context"
	"errors"
	"reflect"
	"testing"
)

func TestAdversarialCreateFailureMustNotReserveOrCommit(t *testing.T) {
	tx := &regressionTransaction{
		createErr: errRegressionOperation,
	}
	service := NewOrderService(&regressionDatabase{tx: tx})

	err := service.PlaceOrder(context.Background(), Order{})
	if !errors.Is(err, errRegressionOperation) {
		t.Fatalf("PlaceOrder() error = %v, want create error", err)
	}

	want := []string{"create", "rollback"}
	if !reflect.DeepEqual(tx.events, want) {
		t.Fatalf("transaction events = %v, want %v", tx.events, want)
	}
}

func TestAdversarialReserveFailureMustNotCommit(t *testing.T) {
	tx := &regressionTransaction{
		reserveErr: errRegressionOperation,
	}
	service := NewOrderService(&regressionDatabase{tx: tx})

	err := service.PlaceOrder(context.Background(), Order{})
	if !errors.Is(err, errRegressionOperation) {
		t.Fatalf("PlaceOrder() error = %v, want reserve error", err)
	}

	want := []string{"create", "reserve", "rollback"}
	if !reflect.DeepEqual(tx.events, want) {
		t.Fatalf("transaction events = %v, want %v", tx.events, want)
	}
}
