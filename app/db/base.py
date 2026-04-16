# Import all the models, so that Base has them before being
# imported by Alembic or used by create_all()

from app.db.session import Base  # noqa

from app.models.user import User  # noqa
from app.models.e_commerce.vendors import Vendor  # noqa
from app.models.e_commerce.products import Product  # noqa
from app.models.e_commerce.product_images import ProductImage  # noqa
from app.models.e_commerce.carts import Cart, CartItem  # noqa
from app.models.e_commerce.orders import Order, OrderItem  # noqa
from app.models.e_commerce.compatibility import Compatibility  # noqa
from app.models.e_commerce.ai_scans import AIScan  # noqa

from app.models.fleet.vehicles import Vehicle  # noqa
from app.models.fleet.drivers import Driver  # noqa
from app.models.fleet.assignments import Assignment  # noqa
from app.models.fleet.trips import Trip  # noqa
