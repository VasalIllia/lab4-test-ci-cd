from behave import given, when, then
from app.eshop import Product


@given('The product with name {name} has availability of {availability}')
def step_given_product_availability(context, name, availability):
    context.product = Product(
        name=name,
        price=10.0,
        available_amount=int(availability)
    )


@when('I check if product is available in amount {amount}')
def step_when_check_availability(context, amount):
    context.is_available_result = context.product.is_available(int(amount))


@then('Product is available')
def step_then_product_is_available(context):
    assert context.is_available_result is True, "Expected product to be available, but got False"


@then('Product is not available')
def step_then_product_is_not_available(context):
    assert context.is_available_result is False, "Expected product to not be available, but got True"
