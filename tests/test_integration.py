import uuid
import boto3
from app.eshop import Product, ShoppingCart, Order, Shipment
import random
from services import ShippingService
from services.repository import ShippingRepository
from services.publisher import ShippingPublisher
from datetime import datetime, timedelta, timezone
from services.config import AWS_ENDPOINT_URL, AWS_REGION, SHIPPING_QUEUE
import pytest


@pytest.mark.parametrize("order_id, shipping_id", [
    ("order_1", "shipping_1"),
    ("order_i2hur2937r9", "shipping_1!!!!"),
    (8662354, 123456),
    (str(uuid.uuid4()), str(uuid.uuid4()))
])
def test_place_order_with_mocked_repo(mocker, order_id, shipping_id):
    mock_repo = mocker.Mock()
    mock_publisher = mocker.Mock()
    shipping_service = ShippingService(mock_repo, mock_publisher)

    mock_repo.create_shipping.return_value = shipping_id

    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )

    order = Order(cart, shipping_service, order_id)
    due_date = datetime.now(timezone.utc) + timedelta(seconds=3)
    actual_shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=due_date
    )

    assert actual_shipping_id == shipping_id, "Actual shipping id must be equal to mock return value"

    mock_repo.create_shipping.assert_called_with(ShippingService.list_available_shipping_type()[
                                                 0], ["Product"], order_id, shipping_service.SHIPPING_CREATED, due_date)
    mock_publisher.send_new_shipping.assert_called_with(shipping_id)


def test_place_order_with_unavailable_shipping_type_fails(dynamo_resource):
    shipping_service = ShippingService(
        ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )
    order = Order(cart, shipping_service)
    shipping_id = None

    with pytest.raises(ValueError) as excinfo:
        shipping_id = order.place_order(
            "Новий тип доставки",
            due_date=datetime.now(timezone.utc) + timedelta(seconds=3)
        )
    assert shipping_id is None, "Shipping id must not be assigned"
    assert "Shipping type is not available" in str(excinfo.value)


def test_when_place_order_then_shipping_in_queue(dynamo_resource):
    shipping_service = ShippingService(
        ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()

    cart.add_product(Product(
        available_amount=10,
        name='Product',
        price=random.random() * 10000),
        amount=9
    )

    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    sqs_client = boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test"
    )
    queue_url = sqs_client.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]
    response = sqs_client.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    messages = response.get("Messages", [])
    assert len(messages) == 1, "Expected 1 SQS message"

    body = messages[0]["Body"]
    assert shipping_id == body

# bottom-up тести


def test_1_repo_create_and_get_shipping(dynamo_resource):
    # Перевірка запису та читання з DynamoDB через Repository
    repo = ShippingRepository()
    due_date = datetime.now(timezone.utc) + timedelta(days=1)

    shipping_id = repo.create_shipping(
        "Нова Пошта", ["prod_1"], "order_1", "created", due_date)
    item = repo.get_shipping(shipping_id)

    assert item is not None, "Запис має бути присутнім у БД"
    assert item["shipping_status"] == "created"
    assert item["shipping_type"] == "Нова Пошта"


def test_2_repo_update_shipping_status(dynamo_resource):
    # Перевірка оновлення статусу в DynamoDB
    repo = ShippingRepository()
    due_date = datetime.now(timezone.utc) + timedelta(days=1)
    shipping_id = repo.create_shipping(
        "Укр Пошта", ["prod_2"], "order_2", "created", due_date)

    repo.update_shipping_status(shipping_id, "in progress")
    item = repo.get_shipping(shipping_id)

    assert item["shipping_status"] == "in progress", "Статус у БД має оновитися"


def test_3_publisher_send_and_poll_message(dynamo_resource):
    # Перевірка відправки та отримання повідомлень з SQS
    publisher = ShippingPublisher()
    test_shipping_id = str(uuid.uuid4())

    publisher.send_new_shipping(test_shipping_id)
    messages = publisher.poll_shipping()

    assert test_shipping_id in messages, "Відправлений ID має повернутися з SQS черги"


# top-down тести
def test_4_service_create_shipping_success(dynamo_resource):
    # Сервіс успішно створює доставку інтеграція Service + DB + SQS
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    due_date = datetime.now(timezone.utc) + timedelta(days=2)

    shipping_id = service.create_shipping(
        "Meest Express", ["prod_3"], "order_3", due_date)

    # Перевіряємо, чи змінився статус після відправки в чергу
    assert service.check_status(shipping_id) == service.SHIPPING_IN_PROGRESS


def test_5_service_create_shipping_invalid_type():
    # Сервіс відхиляє неіснуючий тип доставки
    service = ShippingService(None, None)
    due_date = datetime.now(timezone.utc) + timedelta(days=1)

    with pytest.raises(ValueError, match="Shipping type is not available"):
        service.create_shipping("Фейкова Пошта", ["p1"], "o1", due_date)


def test_6_service_create_shipping_past_due_date():
    # Сервіс відхиляє доставку з датою в минулому
    service = ShippingService(None, None)
    past_date = datetime.now(timezone.utc) - timedelta(days=1)

    with pytest.raises(ValueError, match="Shipping due datetime must be greater than datetime now"):
        service.create_shipping("Самовивіз", ["p1"], "o1", past_date)


def test_7_service_process_shipping_completes_if_on_time(dynamo_resource):
    # Успішне завершення доставки, якщо час ще не вийшов
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    due_date = datetime.now(timezone.utc) + timedelta(days=1)

    shipping_id = service.repository.create_shipping(
        "Нова Пошта", ["p1"], "o1", service.SHIPPING_IN_PROGRESS, due_date)
    service.process_shipping(shipping_id)

    assert service.check_status(shipping_id) == service.SHIPPING_COMPLETED


def test_8_service_process_shipping_fails_if_late(dynamo_resource):
    # Провал доставки, якщо дедлайн протерміновано
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    due_date = datetime.now(timezone.utc) - timedelta(days=1)

    shipping_id = service.repository.create_shipping(
        "Укр Пошта", ["p1"], "o1", service.SHIPPING_IN_PROGRESS, due_date)
    service.process_shipping(shipping_id)

    assert service.check_status(shipping_id) == service.SHIPPING_FAILED


def test_9_order_place_order_integration(dynamo_resource):
    # Розміщення замовлення створює доставку в БД та черзі SQS
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product("Iphone", 1000, 5), amount=1)
    order = Order(cart, service)
    due_date = datetime.now(timezone.utc) + timedelta(days=3)

    shipping_id = order.place_order("Самовивіз", due_date)

    assert shipping_id is not None
    assert service.check_status(shipping_id) == service.SHIPPING_IN_PROGRESS


def test_10_shipment_check_status_integration(dynamo_resource):
    # Клас Shipment коректно отримує статус з DynamoDB через Service
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    due_date = datetime.now(timezone.utc) + timedelta(days=1)

    shipping_id = service.repository.create_shipping(
        "Meest Express", ["p1"], "o1", "created", due_date)
    shipment = Shipment(shipping_id, service)

    assert shipment.check_shipping_status() == "created"
