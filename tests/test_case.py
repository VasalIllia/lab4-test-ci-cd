import unittest
from app.eshop import Product, ShoppingCart, Order
from unittest.mock import MagicMock


class TestProduct(unittest.TestCase):
    def setUp(self):
        self.product = Product(name='Test', price=123.45, available_amount=21)
        self.cart = ShoppingCart()

    def tearDown(self):
        self.cart.remove_product(self.product)

    def test_mock_add_product(self):
        self.product.is_available = MagicMock()
        self.cart.add_product(self.product, 12345)
        self.product.is_available.assert_called_with(12345)
        self.product.is_available.reset_mock()

    def test_add_available_amount(self):
        self.cart.add_product(self.product, 11)
        self.assertEqual(self.cart.contains_product(self.product), True,'Продукт має успішно додатися до корзини, якщо його достатньо на складі')

    def test_add_non_available_amount(self):
        with self.assertRaises(ValueError, msg='Очікувався ValueError при спробі додати кількість, що перевищує наявну'):
            self.cart.add_product(self.product, 22)

        self.assertEqual(self.cart.contains_product(self.product), False,msg='Продукт не повинен бути доданий до корзини через нестачу кількості')


class TestEShop(unittest.TestCase):
    def setUp(self):
        self.product1 = Product(
            name='Laptop', price=1000.0, available_amount=5)
        self.product2 = Product(name='Mouse', price=50.0, available_amount=10)
        self.cart = ShoppingCart()

    def test_product_is_available_true(self):
        # Чи повертає Product True, якщо товару достатньо
        self.assertTrue(self.product1.is_available(3), msg="Товар має бути доступним, оскільки запитується 3 одиниці, в наявності 5")
        self.assertTrue(self.product1.is_available(5), msg="Товар має бути доступним при запиті граничної кількості рівно 5 одиниць")

    def test_product_is_available_false(self):
        # Чи повертає Product False, якщо запитується забагато
        self.assertFalse(self.product1.is_available(6),msg="Метод is_available має повернути False, бо запитується 6 одиниць, в наявності лише 5")

    def test_product_buy_decreases_amount(self):
        # Чи коректно метод buy зменшує залишок товару.
        self.product1.buy(2)
        self.assertEqual(self.product1.available_amount, 3,msg="Залишок товару після покупки 2 одиниць має дорівнювати 3, 5-2")

    def test_product_equality(self):
        # Чи правильно працюють магічні методи порівняння для Product
        product_same_name = Product(
            name='Laptop', price=1200.0, available_amount=1)
        product_diff_name = Product(
            name='Keyboard', price=100.0, available_amount=5)

        self.assertEqual(self.product1, product_same_name, msg="Товари з однаковим ім'ям Laptop мають вважатися рівними")
        self.assertNotEqual(self.product1, product_diff_name,msg="Товари з різними іменами не мають вважатися рівними")

    def test_cart_add_product_type_error(self):
        # Чи викликається TypeError, якщо кількість дорівнює None
        with self.assertRaises(TypeError, msg="Очікувався TypeError, оскільки передано None"):
            self.cart.add_product(self.product1, None)

    def test_cart_add_existing_product_updates_amount(self):
        # Чи сумується кількість, якщо додавати той самий товар у корзину кілька разів
        self.cart.add_product(self.product1, 2)
        self.cart.add_product(self.product1, 1)
        self.assertEqual(self.cart.products[self.product1], 3, msg="Кількість товару в корзині має коректно підсумовуватися 2+1 = 3")

    def test_cart_calculate_total(self):
        # Чи правильно рахується загальна вартість корзини
        self.cart.add_product(self.product1, 2)
        self.cart.add_product(self.product2, 3)
        self.assertEqual(self.cart.calculate_total(
        ), 2150.0, msg="Загальна вартість розрахована неправильно очікувалося 2000+150 = 2150.0")

    def test_cart_remove_product(self):
        # Чи успішно видаляється товар із корзини.
        self.cart.add_product(self.product1, 2)
        self.cart.remove_product(self.product1)
        self.assertFalse(self.cart.contains_product(
            self.product1), msg="Товар не був видалений з корзини після виклику remove_product")

    def test_cart_submit_order_clears_cart_and_buys(self):
        # Чи submit_cart_order зменшує кількість товарів і очищає корзину
        self.cart.add_product(self.product1, 2)
        self.cart.submit_cart_order()

        self.assertEqual(self.product1.available_amount, 3,msg="Кількість товару на складі не зменшилася після оформлення замовлення")
        self.assertEqual(len(self.cart.products), 0,msg="Корзина має бути порожньою після виклику submit_cart_order")

    def test_order_place_order_calls_submit(self):
        # Чи делегує Order виклик до ShoppingCart за допомогою Mock
        self.cart.submit_cart_order = MagicMock()
        order = Order(self.cart)
        order.place_order()

        self.cart.submit_cart_order.assert_called_once()


if __name__ == '__main__':
    unittest.main()
