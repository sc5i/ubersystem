from uber import config
from uber.tests import *


class TestPrices:
    def test_initial_attendee(self, clear_price_bumps):
        assert 40 == c.get_attendee_price(datetime.now(UTC))

    def test_group_member(self, clear_price_bumps):
        assert 30 == c.get_group_price(datetime.now(UTC))


class TestPriceBumps:
    @pytest.fixture(autouse=True)
    def add_price_bump_day(request, monkeypatch):
        monkeypatch.setattr(c, 'PRICE_BUMPS', {(datetime.now(UTC) - timedelta(days=1)): 50})
        monkeypatch.setattr(c, 'PRICE_LIMITS', {})

    def test_after_date_price_bump(self):
        assert 50 == c.get_attendee_price(datetime.now(UTC))

    def test_before_date_no_price_bump(self):
        assert 40 == c.get_attendee_price((datetime.now(UTC) - timedelta(days=2)))

    def test_on_date_no_price_bump(self):
        assert 40 == c.get_attendee_price((datetime.now(UTC) - timedelta(days=1, hours=2)))


class TestPriceLimits:
    @pytest.fixture(autouse=True)
    def add_price_bump_limit(request, monkeypatch):
        monkeypatch.setattr(c, 'PRICE_LIMITS', {1: 50})
        monkeypatch.setattr(c, 'PRICE_BUMPS', {})

    def test_under_limit_no_price_bump(self):
        assert 40 == c.get_attendee_price()

    def test_over_limit_price_bump_before_event(self, monkeypatch):
        monkeypatch.setattr(c, 'EPOCH', localized_now() + timedelta(days=1))
        session = Session().session
        assert c.BADGES_SOLD == 0

        with request_cached_context():
            session.add(Attendee(paid=c.HAS_PAID, badge_status=c.COMPLETED_STATUS))
            session.commit()

        assert c.BADGES_SOLD == 1
        assert 50 == c.get_attendee_price()

    def test_over_limit_price_bump_during_event(self, monkeypatch):
        monkeypatch.setattr(c, 'EPOCH', localized_now() - timedelta(days=1))

        session = Session().session
        assert c.BADGES_SOLD == 0

        with request_cached_context():
            session.add(Attendee(paid=c.HAS_PAID, badge_status=c.COMPLETED_STATUS))
            session.commit()

        assert c.BADGES_SOLD == 1
        assert 40 == c.get_attendee_price()

    def test_refunded_badge_price_bump_before_event(self, monkeypatch):
        monkeypatch.setattr(c, 'EPOCH', localized_now() + timedelta(days=1))
        session = Session().session
        assert c.BADGES_SOLD == 0

        with request_cached_context():
            session.add(Attendee(paid=c.REFUNDED, badge_status=c.COMPLETED_STATUS))
            session.commit()

        assert c.BADGES_SOLD == 1
        assert 50 == c.get_attendee_price()

    def test_refunded_badge_price_bump_during_event(self, monkeypatch):
        monkeypatch.setattr(c, 'EPOCH', localized_now() - timedelta(days=1))
        session = Session().session
        assert c.BADGES_SOLD == 0

        with request_cached_context():
            session.add(Attendee(paid=c.REFUNDED, badge_status=c.COMPLETED_STATUS))
            session.commit()

        assert c.BADGES_SOLD == 1
        assert 40 == c.get_attendee_price()

    def test_invalid_badge_no_price_bump(self):
        session = Session().session
        assert c.BADGES_SOLD == 0

        with request_cached_context():
            session.add(Attendee(paid=c.HAS_PAID, badge_status=c.INVALID_STATUS))
            session.commit()

        assert c.BADGES_SOLD == 0
        assert 40 == c.get_attendee_price()

    def test_free_badge_no_price_bump(self):
        session = Session().session
        assert c.BADGES_SOLD == 0

        with request_cached_context():
            session.add(Attendee(paid=c.NEED_NOT_PAY, badge_status=c.COMPLETED_STATUS))
            session.commit()

        assert c.BADGES_SOLD == 0
        assert 40 == c.get_attendee_price()

    # todo: Test badges that are paid by group


class TestBadgePriceEstimate:
    @pytest.fixture(autouse=True)
    def add_price_limits(request, monkeypatch):
        monkeypatch.setattr(c, 'PRICE_LIMITS', {1000: 50, 2500: 55})
        monkeypatch.setattr(c, 'ORDERED_PRICE_LIMITS', [50, 55])
        monkeypatch.setattr(c, 'PRICE_BUMPS', {})

    def test_no_limits_estimate_no_max(self, monkeypatch):
        monkeypatch.setattr(c, 'ORDERED_PRICE_LIMITS', [])
        monkeypatch.setattr(c, 'MAX_BADGE_SALES', 0)
        assert 'Limitless' == c.BADGES_LEFT_AT_CURRENT_PRICE

    def test_no_limits_estimate_with_max(self, monkeypatch):
        monkeypatch.setattr(c, 'ORDERED_PRICE_LIMITS', [])
        monkeypatch.setattr(c, 'MAX_BADGE_SALES', 100)
        assert 'Very Low' == c.BADGES_LEFT_AT_CURRENT_PRICE

    def test_last_price_estimate_no_max(self, monkeypatch):
        monkeypatch.setattr(uber.config.Config, 'BADGE_PRICE', 55)
        monkeypatch.setattr(c, 'MAX_BADGE_SALES', 0)
        assert 'Limitless' == c.BADGES_LEFT_AT_CURRENT_PRICE

    def test_last_price_estimate_with_max(self, monkeypatch):
        monkeypatch.setattr(uber.config.Config, 'BADGE_PRICE', 55)
        monkeypatch.setattr(c, 'MAX_BADGE_SALES', 100)
        assert 'Very Low' == c.BADGES_LEFT_AT_CURRENT_PRICE

    def test_hardcore_optimized_estimate(self, monkeypatch):
        monkeypatch.setattr(c, 'HARDCORE_OPTIMIZATIONS_ENABLED', True)
        assert 'Unknown' == c.BADGES_LEFT_AT_CURRENT_PRICE

    def test_almost_gone_estimate(self, monkeypatch):
        monkeypatch.setattr(uber.config.Config, 'BADGES_SOLD', 990)
        assert 'Almost Gone' == c.BADGES_LEFT_AT_CURRENT_PRICE

    def test_very_low_estimate(self, monkeypatch):
        monkeypatch.setattr(uber.config.Config, 'BADGES_SOLD', 910)
        assert 'Very Low' == c.BADGES_LEFT_AT_CURRENT_PRICE

    def test_low_estimate(self, monkeypatch):
        monkeypatch.setattr(uber.config.Config, 'BADGES_SOLD', 760)
        assert 'Low' == c.BADGES_LEFT_AT_CURRENT_PRICE

    def test_moderate_estimate(self, monkeypatch):
        monkeypatch.setattr(uber.config.Config, 'BADGES_SOLD', 600)
        assert 'Medium' == c.BADGES_LEFT_AT_CURRENT_PRICE

    def test_high_estimate(self, monkeypatch):
        monkeypatch.setattr(uber.config.Config, 'BADGES_SOLD', 260)
        assert 'High' == c.BADGES_LEFT_AT_CURRENT_PRICE

    def test_very_high_estimate(self, monkeypatch):
        monkeypatch.setattr(uber.config.Config, 'BADGES_SOLD', 60)
        assert 'Very High' == c.BADGES_LEFT_AT_CURRENT_PRICE

    def test_super_high_estimate(self, monkeypatch):
        monkeypatch.setattr(uber.config.Config, 'BADGES_SOLD', 1010)
        monkeypatch.setattr(uber.config.Config, 'BADGE_PRICE', 50)
        assert 'Super High' == c.BADGES_LEFT_AT_CURRENT_PRICE


class TestBadgeOpts:
    def test_prereg_badge_opts_with_group(self, monkeypatch):
        monkeypatch.setattr(c, 'GROUP_PREREG_TAKEDOWN', localized_now() + timedelta(days=1))
        assert c.PREREG_BADGE_TYPES == [c.ATTENDEE_BADGE, c.PSEUDO_DEALER_BADGE, c.PSEUDO_GROUP_BADGE]

    def test_prereg_badge_opts_no_group(self):
        assert c.PREREG_BADGE_TYPES == [c.ATTENDEE_BADGE, c.PSEUDO_DEALER_BADGE]

    def test_prereg_badge_opts_with_extra(self, monkeypatch):
        monkeypatch.setattr(c, 'BADGE_TYPE_PRICES', {c.SUPPORTER_BADGE: 55})
        assert c.PREREG_BADGE_TYPES == [c.ATTENDEE_BADGE, c.PSEUDO_DEALER_BADGE, c.SUPPORTER_BADGE]

    def test_at_door_badge_opts_plain(self, monkeypatch):
        monkeypatch.setattr(c, 'ONE_DAYS_ENABLED', False)
        assert dict(c.AT_THE_DOOR_BADGE_OPTS).keys() == {c.ATTENDEE_BADGE}

    def test_at_door_badge_opts_simple_one_days(self):
        assert dict(c.AT_THE_DOOR_BADGE_OPTS).keys() == {c.ATTENDEE_BADGE, c.ONE_DAY_BADGE}

    def test_at_door_badge_opts_presold_one_days(self, monkeypatch):
        monkeypatch.setattr(c, 'PRESELL_ONE_DAYS', True)
        monday_after_now = localized_now() + timedelta(days=(7-localized_now().weekday()))
        monkeypatch.setattr(c, 'EPOCH', monday_after_now + timedelta(days=4))
        monkeypatch.setattr(c, 'ESCHATON', monday_after_now + timedelta(days=6))
        assert dict(c.AT_THE_DOOR_BADGE_OPTS).keys() == {c.ATTENDEE_BADGE, c.FRIDAY, c.SATURDAY, c.SUNDAY}

    def test_at_door_badge_opts_with_extra(self, monkeypatch):
        monkeypatch.setattr(c, 'BADGE_TYPE_PRICES', {c.SUPPORTER_BADGE: 55})
        assert dict(c.AT_THE_DOOR_BADGE_OPTS).keys() == {c.ATTENDEE_BADGE, c.ONE_DAY_BADGE, c.SUPPORTER_BADGE}


class TestStaffGetFood:
    def test_job_locations_with_food_prep(self):
        assert c.STAFF_GET_FOOD

    def test_job_locations_without_food_prep(self, monkeypatch):
        job_locations = dict(c.JOB_LOCATIONS)
        del job_locations[c.FOOD_PREP]
        monkeypatch.setattr(c, 'JOB_LOCATIONS', job_locations)
        assert not c.STAFF_GET_FOOD


class TestDealerConfig:
    def test_dealer_reg_open(self, monkeypatch):
        monkeypatch.setattr(c, 'DEALER_REG_START', localized_now() - timedelta(days=1))
        monkeypatch.setattr(c, 'DEALER_REG_SHUTDOWN', localized_now() + timedelta(days=1))
        assert c.DEALER_REG_OPEN

    def test_dealer_reg_not_soft_closed(self, monkeypatch):
        monkeypatch.setattr(c, 'DEALER_REG_DEADLINE', localized_now() + timedelta(days=1))
        monkeypatch.setattr(uber.config.Config, 'DEALER_APPS', 10)
        monkeypatch.setattr(c, 'MAX_DEALER_APPS', 100)
        assert not c.DEALER_REG_SOFT_CLOSED

    def test_dealer_reg_not_soft_closed_no_max(self, monkeypatch):
        monkeypatch.setattr(c, 'DEALER_REG_DEADLINE', localized_now() + timedelta(days=1))
        monkeypatch.setattr(uber.config.Config, 'DEALER_APPS', 10)
        monkeypatch.setattr(c, 'MAX_DEALER_APPS', 0)
        assert not c.DEALER_REG_SOFT_CLOSED

    def test_dealer_reg_soft_closed_optimizations(self, monkeypatch):
        monkeypatch.setattr(c, 'DEALER_REG_DEADLINE', localized_now() - timedelta(days=1))
        monkeypatch.setattr(c, 'HARDCORE_OPTIMIZATIONS_ENABLED', True)
        assert c.DEALER_REG_SOFT_CLOSED

    def test_dealer_reg_not_soft_closed_optimizations(self, monkeypatch):
        monkeypatch.setattr(c, 'DEALER_REG_DEADLINE', localized_now() + timedelta(days=1))
        monkeypatch.setattr(uber.config.Config, 'DEALER_APPS', 10)
        monkeypatch.setattr(c, 'MAX_DEALER_APPS', 1)
        monkeypatch.setattr(c, 'HARDCORE_OPTIMIZATIONS_ENABLED', True)
        assert not c.DEALER_REG_SOFT_CLOSED

    def test_dealer_reg_soft_closed_over_max(self, monkeypatch):
        monkeypatch.setattr(c, 'DEALER_REG_DEADLINE', localized_now() + timedelta(days=1))
        monkeypatch.setattr(uber.config.Config, 'DEALER_APPS', 10)
        monkeypatch.setattr(c, 'MAX_DEALER_APPS', 1)
        assert c.DEALER_REG_SOFT_CLOSED

    def test_dealer_reg_soft_closed_at_max(self, monkeypatch):
        monkeypatch.setattr(c, 'DEALER_REG_DEADLINE', localized_now() + timedelta(days=1))
        monkeypatch.setattr(uber.config.Config, 'DEALER_APPS', 1)
        monkeypatch.setattr(c, 'MAX_DEALER_APPS', 1)
        assert c.DEALER_REG_SOFT_CLOSED

    def test_dealer_reg_soft_closed_after_deadline(self, monkeypatch):
        monkeypatch.setattr(c, 'DEALER_REG_DEADLINE', localized_now() - timedelta(days=1))
        monkeypatch.setattr(uber.config.Config, 'DEALER_APPS', 10)
        monkeypatch.setattr(c, 'MAX_DEALER_APPS', 100)
        assert c.DEALER_REG_SOFT_CLOSED

    def test_dealer_app(self):
        session = Session().session
        with request_cached_context():
            session.add(Group(tables=1, cost=10, status=c.UNAPPROVED))
            session.commit()

        assert c.DEALER_APPS == 1

    def test_waitlisted_dealer_not_app(self):
        session = Session().session
        with request_cached_context():
            session.add(Group(tables=1, cost=10, status=c.WAITLISTED))
            session.commit()

        assert c.DEALER_APPS == 0

    def test_free_dealer_no_app(self):
        session = Session().session
        with request_cached_context():
            session.add(Group(tables=1, cost=0, auto_recalc=False, status=c.UNAPPROVED))
            session.commit()

        assert c.DEALER_APPS == 0

    def test_not_a_dealer_no_app(self):
        session = Session().session
        with request_cached_context():
            session.add(Group(tables=0, cost=10, status=c.UNAPPROVED))
            session.commit()

        assert c.DEALER_APPS == 0
