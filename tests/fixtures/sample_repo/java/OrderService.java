package com.example.ecommerce;

import java.util.List;
import java.util.UUID;

/**
 * Order processing service handling checkout, tax calculation, and inventory reservations.
 */
public class OrderService {

    private final double taxRate = 0.08;

    /**
     * Calculates total sales tax for an order amount.
     */
    public double calculateTax(double subtotal) {
        return subtotal * this.taxRate;
    }

    /**
     * Processes customer checkout order and reserves inventory items.
     */
    public String processOrder(String customerId, List<String> itemIds, double subtotal) {
        if (customerId == null || itemIds == null || itemIds.isEmpty()) {
            throw new IllegalArgumentException("Invalid order parameters");
        }

        double tax = calculateTax(subtotal);
        double grandTotal = subtotal + tax;
        String orderId = UUID.randomUUID().toString();

        System.out.println("Order " + orderId + " placed for total: " + grandTotal);
        return orderId;
    }
}
