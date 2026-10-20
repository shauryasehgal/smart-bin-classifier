
def validate_order(ordered_quantities, predicted_quantities):
    """
    Compare ordered quantities against predicted bin quantities.

    ordered_quantities: dict mapping ASIN to requested quantity
    predicted_quantities: dict mapping ASIN to predicted quantity

    Extra products in the bin that are not in the order are ignored.
    """

    results = []
    overall_pass = True

    for asin, ordered_qty in ordered_quantities.items():
        found_qty = predicted_quantities.get(asin, 0)

        passed = found_qty == ordered_qty

        results.append({
            "asin": asin,
            "ordered_quantity": ordered_qty,
            "found_quantity": found_qty,
            "status": "PASS" if passed else "FAIL"
        })

        if not passed:
            overall_pass = False

    return {
        "items": results,
        "overall_status": "PASS" if overall_pass else "FAIL"
    }
