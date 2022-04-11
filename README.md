# VendingProject
Vending Machine API

# Brief
API vending machine, for allowing users with a “seller” role to add, update or remove products, while users with a “buyer” role can deposit coins into the machine and make purchases. Vending machine only accept 5, 10, 20, 50 and 100 cent coins.

**Tasks**

1. REST API should be implemented consuming and producing “application/json”
- Implement product model with amountAvailable, cost (should be in multiples of 5), productName and sellerId fields
- Implement user model with username, password, deposit and role fields
- Implement an authentication method (basic, oAuth, JWT or something else, the choice is yours)
- All of the endpoints should be authenticated unless stated otherwise
- Implement CRUD for users (POST /user should not require authentication to allow new user registration)
- Implement CRUD for a product model (GET can be called by anyone, while POST, PUT and DELETE can be called only by the seller user who created the product)
- Implement /deposit endpoint so users with a “buyer” role can deposit only 5, 10, 20, 50 and 100 cent coins into their vending machine account (one coin at the time)
- Implement /buy endpoint (accepts productId, amount of products) so users with a “buyer” role can buy a product (shouldn't be able to buy multiple different products at the same time) with the money they’ve deposited. API should return total they’ve spent, the product they’ve purchased and their change if there’s any (in an array of 5, 10, 20, 50 and 100 cent coins)
- Implement /reset endpoint so users with a “buyer” role can reset their deposit back to 0
- Take time to think about possible edge cases and access issues that should be solved

**Additional**

- Language/Framework: Python and Django
- Edge cases are covered in [EDGE.md](EDGE.md)
- Write tests for /deposit, /buy and one CRUD endpoint of your choice
- Code readability and optimization

**Bonus:**

- If somebody is already logged in with the same credentials, the user should be given a message "There is already an active session using your account". In this case the user should be able to terminate all the active sessions on their account via an endpoint i.e. /logout/all
- Attention to security

# Edge Cases
Edge cases are covered in [EDGE.md](EDGE.md)
