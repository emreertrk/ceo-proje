import numpy as np
import pandas as pd

REVIEW_COSTS = {1: 100, 2: 50, 3: 40, 4: 0, 5: 0}
SALES_FEE_RATE = 0.10
SUBSCRIPTION_PER_MONTH = 80
IT_ALPHA = 3157.27
IT_BETA = 978.23


def haversine_distance(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * np.arcsin(np.sqrt(a))


def it_costs(n_sellers, n_items, alpha=IT_ALPHA, beta=IT_BETA):
    return alpha * np.sqrt(n_sellers) + beta * np.sqrt(n_items)


def removal_scenarios(sellers, rank_col="net_contribution", alpha=IT_ALPHA, beta=IT_BETA, review_cost_factor=1.0):
    ranked = sellers.sort_values(rank_col, ascending=True).reset_index(drop=True)
    revenues = ranked["revenues"].to_numpy()
    review_costs = ranked["cost_of_reviews"].to_numpy() * review_cost_factor
    items = ranked["quantity"].to_numpy()

    removed_revenues = np.concatenate([[0], np.cumsum(revenues)])
    removed_review_costs = np.concatenate([[0], np.cumsum(review_costs)])
    removed_items = np.concatenate([[0], np.cumsum(items)])

    n_removed = np.arange(len(ranked) + 1)
    kept_sellers = len(ranked) - n_removed
    kept_items = items.sum() - removed_items
    kept_revenues = revenues.sum() - removed_revenues
    kept_review_costs = review_costs.sum() - removed_review_costs
    kept_it = it_costs(kept_sellers, kept_items, alpha, beta)

    return pd.DataFrame({
        "n_removed": n_removed,
        "n_sellers": kept_sellers,
        "n_items": kept_items,
        "revenues": kept_revenues,
        "cost_of_reviews": kept_review_costs,
        "it_costs": kept_it,
        "profit_before_it": kept_revenues - kept_review_costs,
        "profit": kept_revenues - kept_review_costs - kept_it,
    })
