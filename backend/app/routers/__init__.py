from . import auth, bookings, resources

ROUTERS = [auth.router, resources.router, bookings.router]
