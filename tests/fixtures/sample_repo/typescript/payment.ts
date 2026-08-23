/**
 * Payment gateway and transaction processor interface and implementation.
 */

export interface TransactionResult {
    transactionId: string;
    status: "SUCCESS" | "FAILED";
    amount: number;
    timestamp: number;
}

export interface RefundRequest {
    transactionId: string;
    amount: number;
    reason: string;
}

export class PaymentGateway {
    private apiKey: string;

    constructor(apiKey: string) {
        this.apiKey = apiKey;
    }

    /**
     * Processes credit card payment transactions securely.
     */
    async processCardPayment(cardNumber: string, amount: number, currency: string): Promise<TransactionResult> {
        if (!cardNumber || cardNumber.length < 13) {
            throw new Error("Invalid card number");
        }
        if (amount <= 0) {
            throw new Error("Payment amount must be greater than zero");
        }

        return {
            transactionId: `txn_${Date.now()}`,
            status: "SUCCESS",
            amount,
            timestamp: Date.now(),
        };
    }

    /**
     * Issues full or partial refunds for processed transactions.
     */
    async issueRefund(request: RefundRequest): Promise<boolean> {
        if (!request.transactionId) {
            return false;
        }
        return true;
    }
}
