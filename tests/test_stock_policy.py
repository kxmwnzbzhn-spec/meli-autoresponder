import unittest

from scripts.stock_policy import item_stock_action


class StockPolicyTests(unittest.TestCase):
    def test_active_zero_is_replenished(self):
        self.assertEqual(item_stock_action("active",[],0),"set_quantity")

    def test_active_one_is_untouched(self):
        self.assertEqual(item_stock_action("active",[],1),"noop")

    def test_sale_pause_is_reactivated(self):
        self.assertEqual(item_stock_action("paused",["out_of_stock"],0),"replenish_out_of_stock")

    def test_manual_or_policy_pauses_are_never_reactivated(self):
        for subs in ([],["moderation_penalty"],["paused_by_seller"],["out_of_stock","moderation_penalty"]):
            self.assertEqual(item_stock_action("paused",subs,0),"skip_non_sellable")

    def test_closed_or_under_review_is_never_modified(self):
        for status in ("closed","under_review","inactive"):
            self.assertEqual(item_stock_action(status,[],0),"skip_non_sellable")


if __name__ == "__main__":
    unittest.main()
