from behave import given, when, then
from app.eshop import Product, ShoppingCart, Order


@given('Product with price {price} and available amount {availability}')
def create_product(context, price, availability):
    context.product = Product(
        name="Product1",
        price=float(price),
        available_amount=int(availability)
    )


@given('Empty cart')
def create_empty_cart(context):
    context.cart = ShoppingCart()


@given('I add product to the cart in amount {amount}')
@when('I add product to the cart in amount {amount}')
def add_product_step(context, amount):
    context.exception = None

    parsed_amount = None if amount == "None" else int(amount)

    try:
        context.cart.add_product(context.product, parsed_amount)
        context.add_successfully = True
    except Exception as e:
        context.exception = e
        context.add_successfully = False


@when('I calculate the total sum')
def calculate_total_step(context):
    context.total = context.cart.calculate_total()


@when('I remove product from the cart')
def remove_product_step(context):
    context.cart.remove_product(context.product)


@when('I confirm the cart order')
def submit_cart_order_step(context):
    context.cart.submit_cart_order()


@when('I place the order')
def place_order_step(context):
    context.order = Order(context.cart)
    context.order.place_order()


@when('I check availability with parameter {value}')
def check_availability(context, value):
    context.exception = None

    parsed_value = None if value == "None" else int(value)

    try:
        context.product.is_available(parsed_value)
    except Exception as e:
        context.exception = e


@then('Product is added successfully')
def assert_added_successfully(context):
    assert getattr(context, 'add_successfully',
                   False) is True, "Product was not added successfully"


@then('ValueError occurs')
def assert_value_error(context):
    assert isinstance(
        context.exception, ValueError), f"Expected ValueError, but got {type(context.exception)}"


@then('TypeError occurs')
def assert_type_error(context):
    assert isinstance(
        context.exception, TypeError), f"Expected TypeError, but got {type(context.exception)}"


@then('Total sum should be {expected_total}')
def assert_total(context, expected_total):
    assert context.total == float(
        expected_total), f"Expected {expected_total}, got {context.total}"


@then('The cart remains empty')
def assert_cart_empty(context):
    assert len(context.cart.products) == 0, "Cart is not empty"


@then('Available amount of product becomes {expected_amount}')
def assert_product_availability(context, expected_amount):
    assert context.product.available_amount == int(
        expected_amount), f"Expected {expected_amount}, got {context.product.available_amount}"
