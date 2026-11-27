# School Uniform Inventory Management System
## Database Design Documentation

**Document Type:** Database Design Specification  
**Version:** 2.0  
**Status:** Revised Design — Pending Client Validation

---

# 1. System Overview

The School Uniform Inventory Management System manages the school's uniform catalog, inventory, student purchases, payment tracking, supplier procurement, supplier deliveries, and uniform collection.

The system is intended for school personnel. Students do not place orders online or maintain system accounts. Personnel create orders, process payments, manage inventory, and release uniforms to students.

The database is designed to maintain historical transaction records while tracking the school's current inventory.

An important distinction in this design is the separation between supplier procurement and student fulfillment:

- Suppliers may deliver stock partially across multiple deliveries.
- Students must receive their complete uniform orders together.
- Inventory reservations are made only when the entire student order can be fulfilled.

## Core Modules

1. User Management
2. Student Records
3. Product Catalog
4. Uniform Sales and Orders
5. Payment Tracking
6. Stock Procurement
7. Supplier Stock Receiving
8. Inventory Movements

---

# 2. Database Structure

## 2.1 Users

**Table:** `users`

Stores the system users who operate the application.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| email | VARCHAR(255) | Unique user email |
| display_name | VARCHAR(255) | User's display name |
| avatar_url | TEXT | Optional profile image |
| created_at | TIMESTAMP | Account creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

**Responsibilities:**
- Identify personnel performing system operations.
- Associate orders and inventory transactions with responsible personnel.
- Provide accountability for operational activities.

## 2.2 Students

**Table:** `students`

Stores student information used when creating uniform orders.

| Column | Type | Description |
|---|---|---|
| student_id | INTEGER | Primary key / student identifier |
| last_name | VARCHAR(100) | Student's last name |
| first_name | VARCHAR(100) | Student's first name |
| middle_initial | VARCHAR(10) | Optional middle initial |
| strand | VARCHAR(50) | Student's academic strand |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

**Responsibilities:**
- Identify students purchasing uniforms.
- Associate uniform orders with the correct student.
- Store the student's academic strand for reference.

Students do not need user accounts because purchases are processed by school personnel.

## 2.3 Product Catalog

### Table: `sizes`

Stores available uniform sizes.

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| name | VARCHAR(10) | Unique size name |

### Table: `uniform_products`

Stores the school's uniform products and their inventory quantities.

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| strand | VARCHAR(50) | Applicable academic strand |
| gender | VARCHAR(20) | Product gender classification |
| name | VARCHAR(100) | Product name |
| size_id | INTEGER | Foreign key referencing `sizes.id` |
| price | DECIMAL(10,2) | Current product price |
| on_hand_quantity | INTEGER | Physical stock currently held |
| reserved_quantity | INTEGER | Stock committed to paid orders awaiting collection |
| is_active | BOOLEAN | Whether the product is available in the catalog |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |

**Responsibilities:**
- Maintain the uniform product catalog.
- Store current product prices.
- Track physical and reserved inventory.
- Allow products to be deactivated without deleting historical records.

**Inventory calculation:**

`available_quantity = on_hand_quantity - reserved_quantity`

Available quantity represents physical stock that has not already been committed to student orders.

The inventory columns must be updated transactionally.

The following conditions must always hold:

- `on_hand_quantity >= 0`
- `reserved_quantity >= 0`
- `reserved_quantity <= on_hand_quantity`

**Product uniqueness:**

The combination of `strand`, `gender`, `name`, and `size_id` is unique.

This prevents duplicate catalog entries for the same product variation.

---

# 3. Uniform Sales and Orders

## 3.1 Uniform Orders

**Table:** `uniform_orders`

Represents a student's uniform purchase.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| student_id | INTEGER | Foreign key referencing `students.student_id` |
| created_by | UUID | Foreign key referencing `users.id` |
| reference_number | VARCHAR(50) | Unique order reference |
| total_amount | DECIMAL(10,2) | Total order amount |
| payment_status | ENUM | Payment state |
| fulfillment_status | ENUM | Order fulfillment state |
| created_at | TIMESTAMP | Order creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| paid_at | TIMESTAMP | Payment timestamp |
| released_at | TIMESTAMP | Collection/release timestamp |

### Payment Status

| Status | Description |
|---|---|
| unpaid | Payment has not been completed |
| paid | Payment has been completed |
| refunded | Payment has been refunded |

### Fulfillment Status

| Status | Description |
|---|---|
| pending | Order has not yet been paid |
| awaiting_stock | Order is paid, but complete stock is unavailable |
| ready_for_pickup | All order items are available and reserved |
| released | The complete order has been handed over to the student |

Payment and fulfillment are separate processes.

A student may pay for an order even when the school does not currently have enough inventory to fulfill the entire order.

In that situation, the order remains `awaiting_stock` until sufficient stock becomes available.

**Important:** An order must never be partially released. All order items must be available and reserved before the order can be released.

## 3.2 Uniform Order Items

**Table:** `uniform_order_items`

Stores the individual products included in an order.

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| order_id | UUID | Foreign key referencing `uniform_orders.id` |
| product_id | INTEGER | Foreign key referencing `uniform_products.id` |
| product_name_snapshot | VARCHAR(100) | Product name at purchase time |
| size_snapshot | VARCHAR(10) | Product size at purchase time |
| unit_price_snapshot | DECIMAL(10,2) | Product price at purchase time |
| quantity | INTEGER | Purchased quantity |
| amount | DECIMAL(10,2) | Total amount for the item |

**Why snapshots are necessary:**

Product names, sizes, and prices may change over time. Historical orders must preserve the information that was valid when the purchase occurred.

Changing a product's current price must not modify the price of an existing order.

**Amount calculation:**

`amount = unit_price_snapshot × quantity`

The order total should be calculated from its order items.

The combination of `order_id` and `product_id` is unique to avoid duplicate product entries in the same order.

---

# 4. Stock Procurement

## 4.1 Stock Orders

**Table:** `stock_orders`

Represents a procurement order placed with a supplier.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| reference_number | VARCHAR(50) | Unique procurement reference |
| created_by | UUID | Foreign key referencing `users.id` |
| status | ENUM | Procurement status |
| ordered_at | TIMESTAMP | Date the stock was ordered |
| updated_at | TIMESTAMP | Last update timestamp |

### Stock Order Status

| Status | Description |
|---|---|
| ordered | Procurement order has been placed, with no stock received yet |
| partially_received | Some quantities have been received, but outstanding quantities remain |
| received | All ordered quantities have been received |
| cancelled | Remaining procurement quantities have been cancelled |

A procurement order can have multiple supplier deliveries.

For example, the school orders 10 uniforms:

- First delivery: 6 uniforms.
- Second delivery: 2 uniforms.
- Third delivery: 2 uniforms.

The procurement order remains `partially_received` until all 10 uniforms have been received.

The status becomes `received` only when every procurement item has been completely received.

A procurement order can also be cancelled before completion. Previously received stock remains in inventory; cancelling the remaining quantities must not reverse earlier receipts.

## 4.2 Stock Order Items

**Table:** `stock_order_items`

Stores the products and quantities included in a procurement order.

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| stock_order_id | UUID | Foreign key referencing `stock_orders.id` |
| product_id | INTEGER | Foreign key referencing `uniform_products.id` |
| ordered_quantity | INTEGER | Total quantity ordered from the supplier |

The combination of `stock_order_id` and `product_id` is unique.

The ordered quantity represents the total quantity expected from the supplier.

It must not be confused with the quantity already received.

---

# 5. Supplier Stock Receiving

## 5.1 Stock Receipts

**Table:** `stock_receipts`

Represents an individual delivery received from a supplier.

One procurement order can have multiple stock receipts.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| stock_order_id | UUID | Foreign key referencing `stock_orders.id` |
| reference_number | VARCHAR(50) | Unique receipt reference |
| received_by | UUID | Foreign key referencing `users.id` |
| received_at | TIMESTAMP | Actual delivery receiving timestamp |
| notes | TEXT | Optional receiving notes |
| created_at | TIMESTAMP | Record creation timestamp |

**Responsibilities:**
- Record individual supplier deliveries.
- Associate deliveries with their original procurement order.
- Identify personnel responsible for receiving stock.
- Maintain a historical record of each delivery.

## 5.2 Stock Receipt Items

**Table:** `stock_receipt_items`

Stores the actual quantities received in an individual delivery.

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| stock_receipt_id | UUID | Foreign key referencing `stock_receipts.id` |
| stock_order_item_id | INTEGER | Foreign key referencing `stock_order_items.id` |
| received_quantity | INTEGER | Actual quantity received in this delivery |

The combination of `stock_receipt_id` and `stock_order_item_id` is unique.

This prevents duplicate entries for the same procurement item within one receiving record.

### Receiving Quantity Calculation

The total received quantity is calculated from all associated receipt items.

`total_received_quantity = SUM(received_quantity)`

The remaining quantity is:

`outstanding_quantity = ordered_quantity - total_received_quantity`

**Example:**

| Delivery | Received | Total Received | Outstanding |
|---|---:|---:|---:|
| First | 6 | 6 | 4 |
| Second | 2 | 8 | 2 |
| Third | 2 | 10 | 0 |

The system must prevent the cumulative received quantity from exceeding the original ordered quantity.

Receipt records must not be deleted or modified through ordinary application operations after inventory has been updated.

---

# 6. Inventory Movements

**Table:** `inventory_movements`

Maintains an audit trail of inventory changes.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| product_id | INTEGER | Foreign key referencing `uniform_products.id` |
| movement_type | ENUM | Type of inventory transaction |
| quantity | INTEGER | Signed quantity change |
| uniform_order_item_id | INTEGER | Optional reference to a sales order item |
| stock_receipt_item_id | INTEGER | Optional reference to a supplier receipt item |
| created_by | UUID | Foreign key referencing `users.id` |
| notes | TEXT | Optional transaction notes |
| created_at | TIMESTAMP | Transaction timestamp |

### Movement Types

| Type | Description | Quantity |
|---|---|---|
| stock_in | Inventory received from supplier | Positive |
| sale | Inventory deducted after complete student collection | Negative |
| adjustment | Manual inventory correction | Positive or negative |

### Inventory Movement Examples

| Operation | Movement Type | Quantity |
|---|---|---:|
| Receive 6 shirts | stock_in | +6 |
| Receive another 4 shirts | stock_in | +4 |
| Release 3 shirts to a student | sale | -3 |
| Correct inventory discrepancy | adjustment | +5 or -5 |

**Important distinction:**

Reserving inventory does not generate a negative inventory movement.

Reservation only changes the `reserved_quantity` field. Physical inventory remains unchanged.

A negative `sale` movement is generated only when the complete student order is actually released.

Inventory movements should be treated as an append-only transaction history. Ordinary application operations should not modify or delete existing movement records.

For adjustments, the system should require an explanation in `notes`.

---

# 7. Core Business Workflows

## 7.1 Creating a Uniform Order

1. Personnel searches for the student.
2. Personnel selects the required uniform products.
3. The system validates that the products are active.
4. The system validates the requested quantities.
5. The system calculates each item's amount.
6. The system calculates the order total.
7. The system creates the order and its associated order items.
8. The system generates a unique order reference.
9. The order is initially marked as `unpaid` and `pending`.

Creating an unpaid order does not automatically reserve inventory.

The order's creation and its associated items must be committed within one database transaction.

## 7.2 Processing Payment

1. Personnel opens the order.
2. The system verifies that the order is eligible for payment.
3. Personnel records the payment.
4. The system locks the relevant product inventory records.
5. The system calculates available quantities for every order item.
6. The system determines whether the complete order can be fulfilled.

**If all items are available:**

1. The system reserves the complete order quantities.
2. The system increases the corresponding `reserved_quantity` values.
3. The system updates `payment_status` to `paid`.
4. The system updates `fulfillment_status` to `ready_for_pickup`.
5. The system records `paid_at`.
6. The transaction commits.

**If one or more items are unavailable:**

1. No inventory is reserved.
2. The system updates `payment_status` to `paid`.
3. The system updates `fulfillment_status` to `awaiting_stock`.
4. The system records `paid_at`.
5. The transaction commits.

Payment must not be rejected merely because the complete stock is unavailable, assuming the business accepts payment before stock fulfillment.

**Important reservation rule:**

The system must never reserve only part of a student order.

For example, if a student orders 10 uniforms but only 6 are available, all 6 remain unreserved for that order.

The order waits until all 10 can be reserved together.

## 7.3 Processing Orders Awaiting Stock

When new supplier stock is received:

1. The system updates physical inventory.
2. The system retrieves eligible paid orders with `awaiting_stock`.
3. The system checks whether the complete quantities of an order are available.
4. If all items are available, the system reserves all required quantities.
5. The system changes the order's fulfillment status to `ready_for_pickup`.
6. If stock remains insufficient, the order stays `awaiting_stock`.

The reservation operation must be transactional.

The system must also use a consistent allocation policy when multiple waiting orders compete for limited stock.

The allocation priority, such as first-paid-first-served, must be confirmed with the client.

## 7.4 Releasing Uniforms to Students

The system supports complete order collection only.

Students cannot collect individual items from an order.

Workflow:

1. Personnel searches for the order using its reference number.
2. The system verifies that payment has been completed.
3. The system verifies that the fulfillment status is `ready_for_pickup`.
4. The system retrieves all associated order items.
5. The system locks the relevant inventory records.
6. The system verifies that the complete order remains reserved.
7. The system deducts the complete order quantities from physical inventory.
8. The system reduces the corresponding reserved quantities.
9. The system creates negative `sale` inventory movements for every released order item.
10. The system marks the order as `released`.
11. The system records `released_at`.
12. The transaction commits.

The release operation must be atomic.

If any item cannot be released, no item should be deducted, and the order must remain available for collection.

## 7.5 Receiving Supplier Stock

1. Personnel opens an existing procurement order.
2. The system verifies that the procurement order is eligible for receiving.
3. Personnel records the actual quantities delivered.
4. The system validates each quantity against the remaining outstanding quantity.
5. The system creates a stock receipt.
6. The system creates the associated stock receipt items.
7. The system increases physical inventory for each received product.
8. The system creates positive `stock_in` inventory movements.
9. The system recalculates the procurement order status.
10. The system commits the transaction.

The system must prevent cumulative receipts from exceeding the original ordered quantities.

Each receipt must update inventory exactly once.

## 7.6 Cancelling a Procurement Order

1. Personnel selects an existing procurement order.
2. The system verifies that it is not already fully received or cancelled.
3. The system changes its status to `cancelled`.
4. Previously received quantities remain in physical inventory.
5. Outstanding quantities are no longer expected from the supplier.
6. No additional inventory movement is generated by cancellation.

A cancelled procurement order must not accept additional supplier receipts.

---

# 8. Important Database Relationships

| Parent Table | Child Table | Relationship |
|---|---|---|
| sizes | uniform_products | One-to-many |
| students | uniform_orders | One-to-many |
| users | uniform_orders | One-to-many |
| uniform_orders | uniform_order_items | One-to-many |
| uniform_products | uniform_order_items | One-to-many |
| users | stock_orders | One-to-many |
| stock_orders | stock_order_items | One-to-many |
| uniform_products | stock_order_items | One-to-many |
| stock_orders | stock_receipts | One-to-many |
| users | stock_receipts | One-to-many |
| stock_receipts | stock_receipt_items | One-to-many |
| stock_order_items | stock_receipt_items | One-to-many |
| uniform_products | inventory_movements | One-to-many |
| users | inventory_movements | One-to-many |
| uniform_order_items | inventory_movements | One-to-many |
| stock_receipt_items | inventory_movements | One-to-many |

---

# 9. Data Integrity and Transaction Requirements

## 9.1 Quantity Validation

- Product inventory quantities must never be negative.
- Order item quantities must be greater than zero.
- Procurement item quantities must be greater than zero.
- Received quantities must be greater than zero.
- Reserved inventory must never exceed physical inventory.
- Cumulative received quantities must never exceed ordered quantities.
- Student orders must be reserved completely or not at all.
- Student orders must be released completely or not at all.

## 9.2 Financial Validation

- Product prices must not be negative.
- Order item amounts must use the historical unit price.
- The order total must match the sum of its order item amounts.
- Payment timestamps should be set when payment is successfully recorded.
- Refunded orders must not remain eligible for collection.

Refund handling and reservation release must be implemented as a dedicated transactional workflow before refunds are enabled.

## 9.3 Transaction Safety

The following operations must use database transactions:

- Creating an order and its items.
- Recording payment.
- Reserving complete student orders.
- Releasing complete student orders.
- Creating supplier receipts.
- Updating physical inventory.
- Updating procurement statuses.
- Applying inventory adjustments.

For operations involving multiple products, inventory records should be locked in a consistent order to reduce deadlock risks.

The application must prevent duplicate payment processing, duplicate stock receipts, and duplicate order releases.

## 9.4 Historical Data Preservation

- Do not physically delete products referenced by historical orders.
- Deactivate products using `is_active`.
- Preserve product snapshots in order items.
- Preserve supplier receiving records.
- Preserve inventory movement history.
- Avoid cascading deletes that remove historical sales or inventory records.

## 9.5 Inventory Consistency

The product inventory columns represent the current inventory state, while `inventory_movements` provides the transaction history.

These representations must remain consistent.

The application should provide an inventory reconciliation process to compare physical inventory against recorded inventory movements.

---

# 10. Assumptions Requiring Client Confirmation

The revised database design relies on the following business assumptions:

1. **Payment timing:** Students may pay even when complete stock is unavailable.
2. **Complete reservation:** Student orders reserve inventory only when every item can be fulfilled.
3. **Complete collection:** Students must collect every item in an order together.
4. **Partial procurement:** Suppliers may deliver procurement orders across multiple deliveries.
5. **Stock allocation:** Paid orders awaiting stock will be prioritized according to an agreed allocation policy.
6. **No physical returns:** Uniform returns are not currently included in the initial design.
7. **Payment lifecycle:** An order has one overall payment state; partial payments and multiple payment attempts are not modeled.
8. **Procurement cancellation:** Previously received quantities remain in inventory when outstanding procurement quantities are cancelled.

These assumptions must be verified with the client before finalizing the database and implementing the corresponding workflows.

---

# 11. Future Considerations

The following are not included in the initial schema but may become necessary depending on operational requirements:

- Payment transaction history and payment methods.
- Order cancellation workflow.
- Refund auditing and inventory reservation release.
- Separate personnel records for payment and release processing.
- Inventory transfers between school buildings.
- Supplier information and supplier management.
- Inventory reconciliation reports.
- Audit logs for sensitive administrative operations.
- Reservation expiration policies.
- Automated order allocation and prioritization.

These should only be introduced when supported by actual business requirements.

---

# 12. Design Summary

The database separates the system into four major operational areas.

**Student and Sales Management**
- `students`
- `uniform_orders`
- `uniform_order_items`

**Product and Inventory Management**
- `sizes`
- `uniform_products`
- `inventory_movements`

**Supplier Procurement and Receiving**
- `stock_orders`
- `stock_order_items`
- `stock_receipts`
- `stock_receipt_items`

**System Users**
- `users`

The central design principles are:

1. Procurement and supplier receiving are separate operations.
2. Supplier deliveries can be partial.
3. Student orders must be fulfilled completely.
4. Inventory reservations only occur when the complete student order is available.
5. Physical inventory changes only when stock is received, sold, or adjusted.
6. Inventory movements preserve an auditable history of stock changes.
7. Payment, fulfillment, procurement, and receiving maintain separate operational states.

The database serves as the source of truth for order records and inventory state. Business rules must be enforced through transactional application logic and reinforced through database constraints wherever possible.

**Design status:** Revised to support partial supplier deliveries and complete student order fulfillment. Finalization remains subject to client validation of payment timing, order prioritization, and refund policies.