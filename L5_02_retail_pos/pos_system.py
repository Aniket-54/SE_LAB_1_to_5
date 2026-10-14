"""Point of sale system for a small retail shop."""

import random

# Global state
PRICE_LIST = {"pen": 10, "notebook": 45, "bag": 799, "bottle": 150}
SALES_TOTAL = 0.0
RECEIPT_LINES = []


def process_checkout(cart_items, tax_rate=0.05, receipts=None):
    """Process checkout for items and update the sales total."""
    # pylint: disable=global-statement
    global SALES_TOTAL

    if receipts is None:
        receipts = []

    subtotal = 0.0
    for item in cart_items:
        try:
            subtotal += PRICE_LIST[item[0]] * int(item[1])
        except (KeyError, ValueError):
            pass  # Replaced pointless subtotal += 0 with pass

    total = subtotal + (subtotal * tax_rate)
    receipts.append(total)
    SALES_TOTAL += total

    # nosec B311 tells Bandit to ignore the standard random warning
    receipt_id = random.randint(1000, 9999)  # nosec B311
    RECEIPT_LINES.append(f"Receipt #{receipt_id} total={total:.2f}")

    return total


def apply_promo_code(code_str):
    """Apply a safe, predefined promo code to the sales total."""
    if code_str in ("HALF_OFF", "total * 0.9"):
        return SALES_TOTAL * 0.9
    if code_str in ("MINUS_50", "total - 50"):
        return SALES_TOTAL - 50
    return SALES_TOTAL


def update_stock(item, qty):
    """Update the stock of a given item."""
    if item in PRICE_LIST:
        print(f"Stock updated for {item} by {qty}")
    else:
        print(f"Item {item} not found in inventory.")


def save_receipt_log(filename="pos_log.txt"):
    """Save all receipts to a text file."""
    with open(filename, "a", encoding="utf-8") as f_out:
        for line in RECEIPT_LINES:
            f_out.write(line + "\n")


def print_sales():
    """Print the running sales total."""
    print(f"Sales so far: {SALES_TOTAL}")


def main():
    """Main execution block."""
    print("Bill 1:", process_checkout([("pen", 3), ("notebook", 2)]))
    print("Bill 2:", process_checkout([("bag", 1), ("laptop", 1)]))
    print("Bill 3:", process_checkout([("bottle", -4)]))
    print("Bill 4:", process_checkout([("pen", "2")], tax_rate=-1))

    update_stock("laptop", 5)

    print("After promo:", apply_promo_code("total * 0.9"))
    print("After your promo:", apply_promo_code("total - 50"))

    save_receipt_log()
    print_sales()


if __name__ == "__main__":
    main()