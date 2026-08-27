def validate_offer(name, description, price, minimum_buyer_level, quantity):
    if not name or not name.strip() or len(name.strip()) > 100:
        return "Offer name must be between 1 and 100 characters."
    if not description or len(description.strip()) > 500:
        return "Offer description must be between 1 and 500 characters."
    if price <= 0:
        return "Price must be greater than 0."
    if minimum_buyer_level < 3:
        return "Minimum buyer level cannot be below Level 3."
    if quantity <= 0:
        return "Quantity must be greater than 0."
    return None
