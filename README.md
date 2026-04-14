# EcoFinds V2 – The Optimised Sustainable Marketplace

Welcome to EcoFinds V2, radically overhauled for production readiness, smooth UX, and impressive architectural patterns.

## Major V2 Improvements (Resume Ready)

1. **Security & Authentication (JWT + OTP)**
   - Replaced basic user ID passing with a robust JWT bearer token system.
   - Introduced a seamless, unified OTP login/signup flow (`auth.html`).

2. **Clean Flask Blueprints Architecture**
   - Refactored the monolithic `app.py` into a highly scalable Flask Application Factory pattern.
   - Data domains are properly separated: `routes/auth.py`, `routes/products.py`, `routes/orders.py`, `routes/cart.py`, and `routes/analytics.py`.
   - Complex `SQLAlchemy` relationships handle Cascades, orders, items, products, multiple images per product, and reviews.

3. **"Wow Factor" Data Engineering**
   - **Seller Analytics**: Implemented a comprehensive Chart.js dashboard measuring Seller Time-Series Revenue, Sales, and active listing counts based on dynamic data via SQL outer JOIN queries.
   - **Carbon CO₂ Footprint Tracker**: Order payloads calculate and aggregate CO2 metric savings for every pre-owned checkout automatically dynamically generating user impact pages.
   - **Scikit-Learn Recommendations (AI)**: Preserved and isolated the TF-IDF Cosine Similarity recommendation feature.
   
4. **Modern UI/UX Aesthetics**
   - Completely revamped `index.html` with deep CSS micro-interactions: Skeleton loading placeholders, UI Glassmorphism, Floating CO2 Badges, Hover states, and beautiful toast orchestrations.
   - Designed a multiple-image swipeable Carousel feature for Product specific deep-dives integrating interactive Review panels.

## How to Run

### Single Command Start (Recommended)
You can run the entire full-stack application (both backend and frontend simultaneously) using the provided Python runner script. It will automatically start the servers, seed the database, and open the EcoFinds website in your default browser:

```bash
cd backend_folder # (or the project root where run.py is located)
pip install -r requirements.txt
python run.py
```

### Manual Start (Alternative)
If you prefer to start them separately:
1. **Backend**: `python app.py`
2. **Frontend**: `npx http-server ./frontend -p 5173`
