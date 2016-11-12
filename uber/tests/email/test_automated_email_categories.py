from uber.tests.email.email_fixtures import *


class FakeModel:
    pass


@pytest.mark.usefixtures("email_subsystem_sane_setup")
class TestAutomatedEmailCategory:
    def test_testing_environment(self, get_test_email_category):
        assert len(AutomatedEmail.instances) == 1
        assert len(AutomatedEmail.queries[Attendee](None)) == 2
        assert not get_test_email_category.unapproved_emails_not_sent

    def test_event_name(self, get_test_email_category):
        assert get_test_email_category.subject == E.SUBJECT_TO_FIND
        assert get_test_email_category.ident == E.IDENT_TO_FIND

    def test_approval_needed_and_we_have_it(self, monkeypatch, set_test_approved_idents, get_test_email_category):
        assert get_test_email_category.is_approved_to_send()
        assert get_test_email_category.unapproved_emails_not_sent is None

        monkeypatch.setattr(get_test_email_category, 'unapproved_emails_not_sent', 0)
        assert get_test_email_category.is_approved_to_send()
        assert get_test_email_category.unapproved_emails_not_sent == 0

    def test_approval_needed_and_we_dont_have_it(self, monkeypatch, get_test_email_category):
        assert not get_test_email_category.is_approved_to_send()
        assert get_test_email_category.unapproved_emails_not_sent is None

        monkeypatch.setattr(get_test_email_category, 'unapproved_emails_not_sent', 0)
        assert not get_test_email_category.is_approved_to_send()
        assert get_test_email_category.unapproved_emails_not_sent == 1

    def test_approval_not_needed(self, monkeypatch, get_test_email_category):
        assert not get_test_email_category.is_approved_to_send()
        monkeypatch.setattr(get_test_email_category, 'needs_approval', False)
        assert get_test_email_category.is_approved_to_send()

    # --------------  test should_send() -------------------

    def test_should_send_goes_through(self, get_test_email_category, set_test_approved_idents, attendee1):
        assert get_test_email_category.should_send(session=None, model_inst=attendee1, previously_sent_emails={})

    def test_should_send_incorrect_model_used(self, monkeypatch, get_test_email_category, attendee1):
        wrong_model=FakeModel()
        assert not get_test_email_category.should_send(session=None, model_inst=wrong_model, previously_sent_emails={})

    def test_should_send_no_email_present(self, monkeypatch, get_test_email_category, attendee1):
        delattr(attendee1, 'email')
        assert not get_test_email_category.should_send(session=None, model_inst=attendee1, previously_sent_emails={})

    def test_should_send_blank_email_present(self, monkeypatch, get_test_email_category, attendee1):
        attendee1.email = ''
        assert not get_test_email_category.should_send(session=None, model_inst=attendee1, previously_sent_emails={})

    def test_should_send_(self, get_test_email_category, set_test_approved_idents, set_previously_sent_emails_to_attendee1, attendee1):
        previously_sent_emails = set_previously_sent_emails_to_attendee1
        assert not get_test_email_category.should_send(session=None, model_inst=attendee1, previously_sent_emails=previously_sent_emails)

    def test_should_send_wrong_filter(self, get_test_email_category, set_test_approved_idents, attendee1):
        get_test_email_category.filter = lambda a: a.paid == c.HAS_PAID
        assert not get_test_email_category.should_send(session=None, model_inst=attendee1, previously_sent_emails={})

    def test_should_send_not_approved(self, get_test_email_category, attendee1):
        assert not get_test_email_category.should_send(session=None, model_inst=attendee1, previously_sent_emails={})
