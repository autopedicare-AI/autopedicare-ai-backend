from enum import Enum

class Role(str, Enum):
    USER = "user"
    VENDOR = "vendor"
    DRIVER = "driver"
    ADMIN = "admin"
    MECHANIC = "mechanic"


class Permission(str, Enum):
    """Permissions"""
    
    # users Permissions
    USERS_READ = "users.read"
    USERS_UPDATE = "users.update"
    USERS_DELETE = "users.delete"
    USERS_VERIFY = "users.verify"
    USERS_DEACTIVATE = "users.deactivate"
    USERS_RESET_SESSION = "users.reset_session"
    
    # Vendors Permissions
    VENDORS_READ = "vendors.read"
    VENDORS_APPROVE = "vendors.approve"
    VENDORS_UPDATE = "vendors.update"
    VENDORS_REJECT = "vendors.reject"
    VENDORS_SUSPEND = "vendors.suspend"
    
    
    # Products Permissions
    PRODUCTS_READ = "products.read"
    PRODUCTS_CREATE = "products.create"
    PRODUCTS_UPDATE = "products.update"
    PRODUCTS_DELETE = "products.delete"
    PRODUCTS_APPROVE = "products.approve"
    PRODUCTS_REJECT = "products.reject"
    
    # orders Permissions
    ORDERS_READ = "orders.read"
    ORDERS_UPDATE = "orders.update"
    ORDERS_CANCEL = "orders.cancel"
    ORDERS_REFUND = "orders.refund"
        
    # Fleet Permissions
    FLEET_READ = "fleet.read"
    FLEET_ASSIGN_DRIVER = "fleet.assign_driver"
    FLEET_UPDATE_STATUS = "fleet.update_status"
    
    # service requests Permissions
    SERVICE_REQUESTS_READ = "service_requests.read"
    SERVICE_REQUESTS_ACCEPT = "service_requests.accept"
    SERVICE_REQUESTS_REJECT = "service_requests.reject"
    SERVICE_REQUESTS_UPDATE = "service_requests.update"
    SERVICE_REQUESTS_COMPLETE = "service_requests.complete"
    
    # Delivery Permissions
    DELIVERY_READ = "delivery.read"
    DELIVERY_ACCEPT = "delivery.accept"
    DELIVERY_REJECT = "delivery.reject"
    DELIVERY_COMPLETE = "delivery.complete"
    
    # Mechanic Permissions
    MECHANIC_READ = "mechanic.read"
    MECHANIC_APPROVE = "mechanic.approve"
    MECHANIC_REJECT = "mechanic.reject"
    MECHANIC_SUSPEND = "mechanic.suspend"
    MECHANIC_UPDATE = "mechanic.update"
    
    # Reports Permissions
    REPORTS_VIEW = "reports.view"
    
    # analytics Permissions
    ANALYTICS_VIEW = "analytics.view"
    
    # Settings Permissions
    SETTINGS_UPDATE = "settings.update"
    AUDIT_VIEW = "audit.view"


ROLE_PERMISSIONS = {
    Role.USER: {
        Permission.USERS_READ,
        Permission.PRODUCTS_READ,
        Permission.ORDERS_READ
    },
    
    Role.VENDOR: {
        Permission.PRODUCTS_CREATE,
        Permission.PRODUCTS_UPDATE,
        Permission.PRODUCTS_DELETE,
        Permission.PRODUCTS_READ,
        
        Permission.ORDERS_READ,
        Permission.ORDERS_UPDATE,
    },
    
    Role.DRIVER: {
        Permission.DELIVERY_READ,
        Permission.DELIVERY_ACCEPT,
        Permission.DELIVERY_REJECT,
        Permission.DELIVERY_COMPLETE,
    },
    
    Role.MECHANIC: {
        Permission.PRODUCTS_READ,
        Permission.SERVICE_REQUESTS_READ,
        Permission.SERVICE_REQUESTS_ACCEPT,
        Permission.SERVICE_REQUESTS_REJECT,
        Permission.SERVICE_REQUESTS_UPDATE,
        Permission.SERVICE_REQUESTS_COMPLETE,
    },
    
    Role.ADMIN: {
        Permission.USERS_READ,
        Permission.USERS_UPDATE,
        Permission.USERS_DELETE,
        Permission.USERS_VERIFY,
        Permission.USERS_DEACTIVATE,
        Permission.USERS_RESET_SESSION,
       
        Permission.VENDORS_READ,
        Permission.VENDORS_APPROVE,
        Permission.VENDORS_UPDATE,
        Permission.VENDORS_REJECT,
        Permission.VENDORS_SUSPEND,
        
        Permission.PRODUCTS_READ,
        Permission.PRODUCTS_CREATE,
        Permission.PRODUCTS_UPDATE,
        Permission.PRODUCTS_DELETE,
        Permission.PRODUCTS_APPROVE,
        Permission.PRODUCTS_REJECT,
        
        Permission.ORDERS_READ, 
        Permission.ORDERS_UPDATE,
        Permission.ORDERS_CANCEL,
        Permission.ORDERS_REFUND,
        
        Permission.FLEET_READ,
        Permission.FLEET_ASSIGN_DRIVER,
        Permission.FLEET_UPDATE_STATUS,  
        
        Permission.REPORTS_VIEW,
        Permission.ANALYTICS_VIEW,
        Permission.SETTINGS_UPDATE,
        Permission.AUDIT_VIEW
    }
}

def get_permissions_for_role(role: Role):
    """Get permissions for a specific role."""
    return ROLE_PERMISSIONS.get(role, set())

def has_permission(role: Role, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in get_permissions_for_role(role)
    