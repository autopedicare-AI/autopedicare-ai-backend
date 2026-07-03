from app.db.session import Base

from app.models.user import User
from app.models.e_commerce.vendors import Vendor
from app.models.e_commerce.products import Product 
from app.models.e_commerce.product_images import ProductImage 
from app.models.e_commerce.carts import Cart, CartItem 
from app.models.e_commerce.orders import Order, OrderItem 
from app.models.e_commerce.compatibility import Compatibility 
from app.models.e_commerce.ai_scans import AIScan 
from app.models.fleet.vehicles import Vehicle 
from app.models.fleet.drivers import Driver 
from app.models.fleet.assignments import Assignment 
from app.models.fleet.trips import Trip 
