Feature: Advanced testing of shopping cart and products
  We want to ensure that the Product, ShoppingCart, and Order classes
  correctly handle both standard and boundary/invalid situations.

  Scenario: 1. Adding the maximum available amount of a product
    Given Product with price 10 and available amount 5
    And Empty cart
    When I add product to the cart in amount 5
    Then Product is added successfully

  Scenario: 2. Exceeding the available product amount by 1
    Given Product with price 10 and available amount 5
    And Empty cart
    When I add product to the cart in amount 6
    Then ValueError occurs

  Scenario: 3. Adding a product in amount 0
    Given Product with price 10 and available amount 5
    And Empty cart
    When I add product to the cart in amount 0
    Then Product is added successfully

  Scenario: 4. Adding a product with a negative amount
    Given Product with price 10 and available amount 5
    And Empty cart
    When I add product to the cart in amount -2
    Then Product is added successfully

  Scenario: 5. Passing None instead of amount when adding
    Given Product with price 10 and available amount 5
    And Empty cart
    When I add product to the cart in amount None
    Then TypeError occurs

  Scenario: 6. Calculating the total sum of an empty cart
    Given Empty cart
    When I calculate the total sum
    Then Total sum should be 0

  Scenario: 7. Removing a product that is not in the cart
    Given Product with price 10 and available amount 5
    And Empty cart
    When I remove product from the cart
    Then The cart remains empty

  Scenario: 8. Confirming the order reduces the available product amount
    Given Product with price 10 and available amount 5
    And Empty cart
    And I add product to the cart in amount 3
    When I confirm the cart order
    Then Available amount of product becomes 2

  Scenario: 9. Placing an order clears the cart
    Given Product with price 10 and available amount 5
    And Empty cart
    And I add product to the cart in amount 2
    When I place the order
    Then The cart remains empty

  Scenario: 10. Checking availability with parameter None
    Given Product with price 10 and available amount 5
    When I check availability with parameter None
    Then TypeError occurs