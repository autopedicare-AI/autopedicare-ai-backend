# AutoPedicare E-commerce API Documentation (Mobile Integration)

This document provides technical details for the mobile developers to integrate the e-commerce functionality of the AutoPedicare backend.

## 1. General Interface Details

- **Base URL:** `/api/v1`
- **Authentication:** Bearer Token (`Authorization: Bearer <JWT>`)
- **Content-Type:** `application/json`

---

## 2. Product Management

### List Products
- **Endpoint:** `GET /products/`
- **Query Params:** `skip` (default 0), `limit` (default 10)
- **Response:** List of products including IDs, prices, stock, and image URLs.

### Get Product Details
- **Endpoint:** `GET /products/{product_id}`
- **Response:** Detailed product object including description, vendor info, and compatibility metadata.

### Filter by Category
- **Endpoint:** `GET /products/category/{category_name}`
- **Description:** Returns products belonging to the specified category.

### Vendor Products
- **Endpoint:** `GET /products/me/{product_id}`
- **Auth:** Required (Vendor only)

---

## 3. Shopping Cart

The cart is managed server-side and linked to the user account.

### View Cart
- **Endpoint:** `GET /cart/`
- **Response:** Cart object containing `items`, `total_amount`, and `item_count`.

### Add to Cart
- **Endpoint:** `POST /cart/items`
- **Body:**
  ```json
  {
    "product_id": "uuid-string",
    "quantity": 1
  }
  ```

### Update Item
- **Endpoint:** `PUT /cart/items/{item_id}`
- **Body:**
  ```json
  {
    "quantity": 2
  }
  ```

### Remove Item
- **Endpoint:** `DELETE /cart/items/{item_id}`

---

## 4. Orders & Checkout

### Checkout
- **Endpoint:** `POST /orders/checkout`
- **Description:** Converts current cart to a pending order.
- **Response:** `OrderResponse` containing `order_id` and `total_amount`.

### Order History
- **Endpoint:** `GET /orders/`
- **Description:** Returns list of all user orders and their current fulfillment status.

---

## 5. Part Compatibility & AI Scanning

### Smart Search
- **Endpoint:** `POST /compatibilities/search`
- **Body:**
  ```json
  {
    "car_brand": "string",
    "car_model": "string",
    "year": "string",
    "engine_type": "string"
  }
  ```

### AI Scanning (Camera)
- **Endpoint:** `POST /scan-parts`
- **Method:** `POST` (Multipart Form-Data)
- **Fields:** 
  - `file`: (Binary image data)
  - `car_brand`: "Toyota"
  - `car_model`: "Camry"
  - `year`: "2020"
- **Returns:** List of product matches based on image recognition.

---

## 6. Payment Flow (Paystack)

### Step 1: Initialize Payment
- **Endpoint:** `POST /pay/{order_id}`
- **Query Param:** `callback_url` (Optional: your mobile deep-link)
- **Returns:** 
  - `authorization_url`: Redirect the user here.
  - `reference`: Save this for verification.

### Step 2: Verification
- **Endpoint:** `GET /pay/verify/{reference}`
- **Description:** Call this AFTER the user returns from the Paystack gateway to confirm payment success.

---

## 7. Status Codes & Errors

- `200/201`: Success
- `400`: Bad Request (Invalid quantity, out of stock)
- `401`: Unauthorized (Invalid or expired token)
- `404`: Resource Not Found
- `502`: Gateway Error (Paystack communication failure)
