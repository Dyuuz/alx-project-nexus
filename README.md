# ALX Nexus E-commerce API

## 🚀 Project Overview

ALX Nexus is a production-ready e-commerce backend API built with Django and Django REST Framework.

The goal of this project was not just to build endpoints, but to design a scalable system that models real-world commerce flows while enforcing business rules at the system layer.

Core Principle:

> Business rules live in the system layer, not in the request layer.

---

## 🎯 Objectives

- Design a secure and scalable RESTful API
- Enforce strict role-based access control
- Model real-world e-commerce lifecycle flows
- Implement production-ready infrastructure features
- Ensure transactional safety across critical operations

---.

## 🔗 Live Project

- 🌍 **Live API:** [Live API](https://stockbridge-m2zc.onrender.com/api/docs/)
- 📘 **API Documentation (Swagger):** [API Docs](https://stockbridge-m2zc.onrender.com/api/redoc/)
- 💻 **GitHub Repository:** [GitHub Repo](https://github.com/Dyuuz/alx-project-nexus)
- 🔗 **Database Design:** [ER Diagram](https://drive.google.com/file/d/1AKN6z0ynnkgOMEMeT2bC_fKdd6JHTozy/view?usp=drivesdk)

---

## 🏗 Architecture Overview

- RESTful API design
- Service-layer–driven business logic
- Thin views/controllers
- Centralized validation and exception handling
- Transaction-safe operations (checkout, order, payment)
- Environment-aware configuration (dev, test, production)

---

## 👤 User & Authentication Model

- CustomUser model with role differentiation (customer, vendor, admin)
- JWT Authentication (access + refresh tokens)
- Role-aware access control
- Designed for extensibility

---

## 🏪 Vendor & Financial Modeling

### Vendor
- One-to-one relationship with CustomUser
- Stores business identity separately

### BankAccount
- One-to-one with Vendor
- Isolated financial details
- Designed for future payout integrations

---

## 📦 Product & Catalog Design

### Category
- Publicly readable
- Admin-controlled

### Product
- Belongs to Vendor and Category
- Stock enforcement handled in service layer
- Prevents overselling
- Pagination enabled for scalable listing

---

## 🛒 Commerce Flow

### Cart
- One active cart per customer
- Automatically created when accessed
- Fully mutable

### CartItem
- Quantity merging
- Safe updates and removals
- No duplicate product entries

### Checkout
- One-to-one with Cart
- Freezes cart state
- Validates eligibility before confirmation

### Order
- One-to-one with Checkout
- Immutable purchase record
- Atomic creation with recovery handling

### Payment
- Linked directly to Order
- Stores amount, method, status, reference
- Provider-agnostic design
- Ready for Stripe/Paystack integration

---

## 🔗 API Endpoints (api/v1/)

### Authentication
- POST /login/

### Users
- POST /users/
- GET /users/
- PATCH /users/{id}/
- DELETE /users/{id}/

### Vendors
- POST /vendors/
- GET /vendors/
- PATCH /vendors/{id}/
- DELETE /vendors/{id}/

### Bank Accounts
- POST /bank-accounts/
- GET /bank-accounts/
- PATCH /bank-accounts/{id}/
- DELETE /bank-accounts/{id}/

### Categories
- GET /categories/
- POST /categories/
- PATCH /categories/{id}/
- DELETE /categories/{id}/

### Products
- GET /products/
- POST /products/
- PATCH /products/{id}/
- DELETE /products/{id}/

### Cart
- GET /cart/

### Cart Items
- POST /cart-items/
- PATCH /cart-items/{id}/
- DELETE /cart-items/{id}/

### Checkout
- GET /checkout/
- PATCH /checkout/update/
- POST /checkout/confirm/

### Orders
- GET /orders/
- POST /orders/create/

### Payments
- GET /payments/
- POST /payments/initiate/
- POST /payments/confirm/

---

## 🛡 Security & Performance

- Scoped rate limiting (risk-based)
- Role-based permissions
- Ownership enforcement
- Redis caching
- Transaction-safe database operations

---

## ⚙ Infrastructure & Tooling

### Backend
- Python
- Django
- Django REST Framework

### Database
- PostgreSQL

### Caching & Async
- Redis
- Celery
- Celery Beat (background scheduler)

### Media Storage
- Cloudinary

### Documentation
- Swagger / OpenAPI

### Testing
- Pytest (unit & integration tests)

### DevOps
- Docker containerization
- CI/CD pipeline
- Cloud deployment (Render)

---

## 🔄 End-to-End Flow

Cart → Checkout (confirmed) → Order → Payment

Each transition is validated and enforced at the system level.  
No step can be skipped or bypassed via direct requests.

---

## 📈 Project Outcome

This project demonstrates:

- Strong system design thinking
- Real-world commerce modeling
- Enforcement of business rules at the system layer
- Production-grade API security
- Scalable and extensible architecture
- Infrastructure readiness for real deployment

---

Built to evolve — not to be rewritten.