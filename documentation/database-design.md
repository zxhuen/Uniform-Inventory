# School Uniform Inventory Management System
## Database Design Documentation

**Document Type:** Database Design Specification  
**Version:** 1.0  
**Status:** Initial Design

---

## 1. System Overview

The School Uniform Inventory Management System manages the school's uniform catalog, inventory, student purchases, payment tracking, supplier procurement, and uniform collection.

The system is intended for school personnel. Students do not place orders online or maintain system accounts. Personnel create orders, record payments, and release uniforms to students.

The database is designed to maintain historical transaction records while tracking the school's current inventory.

### Core Modules

1. User Management
2. Student Records
3. Product Catalog
4. Uniform Sales and Orders
5. Payment Tracking
6. Stock Procurement
7. Inventory Movements

---

## 2. Database Structure

### 2.1 Users

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
- Associate orders and inventory transactions with the personnel responsible.
- Provide accountability for operational activities.

### 2.2 Students

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

### 2.3 Product Catalog

**Table:** `sizes`

Stores available uniform sizes.

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| name | VARCHAR(10) | Unique size name |

**Table:** `uniform_products`

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

The available quantity represents stock that has not already been committed to pending paid orders.

The `on_hand_quantity` and `reserved_quantity` fields must be updated transactionally. They must not become negative, and reserved quantity must never exceed physical stock.

**Product uniqueness:**

The combination of `strand`, `gender`, `name`, and `size_id` is unique. This prevents duplicate catalog entries for the same product variation.

---

## 3. Uniform Sales and Orders

### 3.1 Uniform Orders

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
| release_status | ENUM | Collection state |
| created_at | TIMESTAMP | Order creation timestamp |
| updated_at | TIMESTAMP | Last update timestamp |
| paid_at | TIMESTAMP | Payment timestamp |
| released_at | TIMESTAMP | Collection/release timestamp |

**Payment status values:**

| Status | Description |
|---|---|
| unpaid | Payment has not been completed |
| paid | Payment has been completed |
| refunded | Payment has been refunded |

**Release status values:**

| Status | Description |
|---|---|
| pending | Uniforms have not yet been collected |
| released | The complete order has been collected |

Payment and collection are separate processes.

A student may pay for an order and collect it at a later date. Therefore, an order can be `paid` while its release status remains `pending`.

### 3.2 Uniform Order Items

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

For example, changing a product's current price must not modify the price of an existing order.

**Amount calculation:**

`amount = unit_price_snapshot × quantity`

The order total should be calculated from its order items.

---

## 4. Stock Procurement

### 4.1 Stock Orders

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

**Stock order status values:**

| Status | Description |
|---|---|
| ordered | Procurement order has been placed |
| received | Complete supplier delivery has been received |
| cancelled | Procurement order has been cancelled |

The current design assumes suppliers deliver all items in a procurement order together. Partial deliveries are not represented.

### 4.2 Stock Order Items

**Table:** `stock_order_items`

Stores the products and quantities included in a procurement order.

| Column | Type | Description |
|---|---|---|
| id | INTEGER | Primary key |
| stock_order_id | UUID | Foreign key referencing `stock_orders.id` |
| product_id | INTEGER | Foreign key referencing `uniform_products.id` |
| quantity | INTEGER | Ordered quantity |

When a procurement order is received, the corresponding product inventory is increased.

The system must prevent a procurement order from being received more than once.

---

## 5. Inventory Movements

**Table:** `inventory_movements`

Maintains an audit trail of inventory changes.

| Column | Type | Description |
|---|---|---|
| id | UUID | Primary key |
| product_id | INTEGER | Foreign key referencing `uniform_products.id` |
| movement_type | ENUM | Type of inventory transaction |
| quantity | INTEGER | Signed quantity change |
| uniform_order_item_id | INTEGER | Optional reference to a sales order item |
| stock_order_item_id | INTEGER | Optional reference to a procurement item |
| created_by | UUID | Foreign key referencing `users.id` |
| notes | TEXT | Optional transaction notes |
| created_at | TIMESTAMP | Transaction timestamp |

**Movement types:**

| Type | Description | Quantity |
|---|---|---|
| stock_in | Inventory received from supplier | Positive |
| sale | Inventory deducted after collection | Negative |
| adjustment | Manual inventory correction | Positive or negative |

### Inventory Movement Examples

| Operation | Movement Type | Quantity |
|---|---|---:|
| Receive 50 shirts | stock_in | +50 |
| Release 3 shirts to a student | sale | -3 |
| Correct an inventory discrepancy | adjustment | +5 or -5 |

Inventory movements should be treated as an append-only transaction history. Ordinary application operations should not modify or delete existing movement records.

The movement history provides traceability for inventory changes.

---

## 6. Core Business Workflows

### 6.1 Creating a Uniform Order

1. Personnel searches for the student.
2. Personnel selects the required uniform products.
3. The system validates product availability.
4. The system calculates each item's amount.
5. The system calculates the order total.
6. The system creates the order and its associated order items.
7. The system generates a unique order reference.
8. The order is initially marked as `unpaid` and `pending`.

**Important:** Creating an unpaid order does not automatically mean inventory has been reserved. The reservation policy must be confirmed with the client.

### 6.2 Processing Payment

Under the proposed reservation policy:

1. Personnel opens the order.
2. The system validates that the order is eligible for payment.
3. The system locks the relevant product inventory records.
4. The system verifies that sufficient available stock exists for every order item.
5. The system reserves the required quantities.
6. The system updates the order's payment status to `paid`.
7. The system records `paid_at`.
8. The transaction commits.

All inventory reservations and payment status changes must succeed together.

If any item lacks sufficient stock, the transaction must fail without partially reserving inventory.

**Reservation calculation:**

`reserved_quantity = reserved_quantity + order_item.quantity`

The physical stock remains unchanged during reservation.

### 6.3 Releasing Uniforms to Students

The system supports complete order collection only. Students cannot collect individual items from an order.

Workflow:

1. Personnel searches for the order using its reference number.
2. The system verifies that the order is paid.
3. The system verifies that the order is still pending collection.
4. The system retrieves all associated order items.
5. The system deducts the complete order quantity from physical inventory.
6. The system reduces the reserved quantities.
7. The system creates negative `sale` inventory movements for the released items.
8. The system marks the order as `released`.
9. The system records `released_at`.
10. The transaction commits.

The release operation must be atomic. If any item cannot be released, no item should be deducted and the order must remain pending.

### 6.4 Receiving Supplier Stock

1. Personnel opens an existing procurement order.
2. The system verifies that its status is `ordered`.
3. Personnel confirms that the complete delivery has arrived.
4. The system increases physical inventory for each procurement item.
5. The system creates positive `stock_in` inventory movements.
6. The system marks the procurement order as `received`.
7. The transaction commits.

The system must prevent the same procurement order from increasing inventory multiple times.

### 6.5 Cancelling a Procurement Order

1. Personnel selects an existing procurement order.
2. The system verifies that it has not already been received.
3. The system changes its status to `cancelled`.
4. No inventory movement is generated.

A received procurement order must not be cancelled through this workflow.

---

## 7. Important Database Relationships

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
| uniform_products | inventory_movements | One-to-many |
| users | inventory_movements | One-to-many |
| uniform_order_items | inventory_movements | One-to-many |
| stock_order_items | inventory_movements | One-to-many |

---

## 8. Data Integrity and Transaction Requirements

The application must enforce the following rules.

### 8.1 Quantity Validation

- Product quantities must be greater than or equal to zero.
- Order item quantities must be greater than zero.
- Procurement item quantities must be greater than zero.
- Reserved inventory must never exceed physical inventory.
- Inventory quantities must not become negative.

### 8.2 Financial Validation

- Product prices must not be negative.
- Order item amounts must be calculated using the historical unit price.
- The order total must match the sum of its order item amounts.
- Payment timestamps should be set when payment is successfully recorded.

### 8.3 Transaction Safety

The following operations must use database transactions:

- Creating an order and its items.
- Processing payment and reserving inventory.
- Releasing an entire order.
- Receiving a procurement order.
- Applying inventory adjustments.

For operations involving multiple products, lock inventory records in a consistent order to reduce deadlock risk.

### 8.4 Historical Data Preservation

- Do not physically delete products that are referenced by historical orders.
- Deactivate products using `is_active`.
- Preserve product snapshots in order items.
- Preserve inventory movement history.
- Avoid cascading deletes that would remove historical sales or inventory records.

### 8.5 Inventory Consistency

The product inventory columns represent the current inventory state, while `inventory_movements` provides the transaction history.

These two representations must remain consistent.

The application should provide a way to reconcile current inventory against the movement history if discrepancies occur.

---

## 9. Assumptions Requiring Client Confirmation

The current database design relies on the following business assumptions:

1. **Payment reservation:** Paid orders reserve their complete inventory quantities immediately, even if students collect later.
2. **Complete collection:** Students must collect every item in an order together.
3. **No physical returns:** Students cannot return purchased uniforms.
4. **Complete procurement delivery:** Suppliers deliver all items in a procurement order together.
5. **No partial supplier receipts:** Procurement orders are received as a complete delivery.
6. **Payment lifecycle:** An order has one overall payment state; partial payments and multiple payment attempts are not currently modeled.

These assumptions should be verified before finalizing the database and implementing the corresponding workflows.

---

## 10. Future Considerations

The following are not included in the initial schema but may become necessary depending on actual operational requirements:

- Payment transaction history and payment methods.
- Order cancellation workflow.
- Refund auditing.
- Separate personnel records for payment and release processing.
- Inventory transfers between school buildings.
- Supplier information and supplier management.
- Inventory reconciliation reports.
- Audit logs for sensitive administrative operations.

These should only be introduced when supported by actual business requirements.

---

## 11. Design Summary

The database separates the system into three major operational areas:

**Sales Management**
- `students`
- `uniform_orders`
- `uniform_order_items`

**Inventory and Procurement**
- `uniform_products`
- `sizes`
- `stock_orders`
- `stock_order_items`
- `inventory_movements`

**System Users**
- `users`

The central design principle is to keep sales, payment, collection, procurement, and inventory changes distinct while maintaining transactional consistency between them.

The database serves as the source of truth for order records and inventory state. Business rules must be enforced by the application and, where possible, reinforced through database constraints.